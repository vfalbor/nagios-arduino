from pysnmp.entity import engine, config
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.entity.rfc3413 import ntforg, context
from pysnmp.proto.api import v2c
#from pysnmp.smi import builder,view
from pysnmp.proto import rfc1902,rfc1155

def S_OK(value=''):
  return {'OK': True, 'Value': value}

def S_ERROR(Message):
  return {'OK': False, 'Message': Message}

class SendTrap(ntforg.NotificationOriginator):
  def __init__(self, mibPath, temperatureValue, snmpRelays, criticalStatus=True):
    from types import ListType, TupleType,StringTypes
    from re import compile,search
    from socket import gethostbyname

    extractPaths=compile(r'[,:]')
    checkIP=compile(r'(\d{1,3}\.){3}\d{1,3}')

    # Create SNMP engine instance
    self.snmpEngine = engine.SnmpEngine()

    if not temperatureValue:
      raise ValueError, 'A temperature must be provided'
    
    self.temperature=temperatureValue
    #print "============>mibPath type: %s" %type(mibPath)
    if type(mibPath) in StringTypes:
      mibPathTuple=tuple(extractPaths.split(mibPath))
    elif type(mibPath) in (ListType, TupleType):
      mibPathTuple=tuple(mibPath)
    else:
      mibPathTuple=('/usr/local/share/snmp/python/',)

    mibBuilder = self.snmpEngine.msgAndPduDsp.mibInstrumController.mibBuilder

    #print mibPathTuple
    mibSources = mibBuilder.getMibPath() + mibPathTuple
    mibBuilder.setMibPath(*mibSources)

    mibBuilder.loadModules( 'USC-IGFAE-MIB' )

    if type(snmpRelays) in StringTypes:
      snmpRelays=snmpRelays.split(',')
    elif not type(snmpRelays) in (ListType,TupleType):
      raise TypeError, 'The list of SNMP relays must be a string or a list or tuple of strings'
    
    
    (temperatureCritical, temperatureOK, self.roomTemp) = mibBuilder.importSymbols('USC-IGFAE-MIB','temperatureCritical', 'temperatureOK', 'roomTemp' )

    # SecurityName <-> CommunityName mapping
    config.addV1System(self.snmpEngine, 'Arduino', 'ups')

    # Specify security settings per SecurityName (SNMPv2c -> 1)
    config.addTargetParams(self.snmpEngine, 'creds', 'Arduino', 'noAuthNoPriv', 0)

    # Setup transport endpoint and bind it with security settings yielding
    # a target name
    config.addSocketTransport(
      self.snmpEngine,
      udp.domainName,
      udp.UdpSocketTransport().openClientMode()
    )

    index=0
    for machine in snmpRelays:
      index=index+1
      if not checkIP.match(machine):
        try:
          machine=gethostbyname(machine)
        except:
          continue

      #print "==============>SNMP relay  IP: %s" % machine
      config.addTargetAddr(
        self.snmpEngine, 'NMS%s' % index,
        udp.domainName, (machine, 162),
        'creds',
        tagList='managers'
      )

    # Specify what kind of notification should be sent (TRAP or INFORM),
    # to what targets (chosen by tag) and what filter should apply to
    # the set of targets (selected by tag)
    config.addNotificationTarget(
      self.snmpEngine, 'sendShutdownTrap', 'my-filter', 'managers', 'trap'
    )

    # Allow NOTIFY access to Agent's MIB by this SNMP model (2), securityLevel
    # and SecurityName
    config.addContext(self.snmpEngine, '')
    config.addVacmUser(self.snmpEngine, 1, 'Arduino', 'noAuthNoPriv',
                       (), (), (1,3,6))

    # *** SNMP engine configuration is complete by this line ***

    # Create default SNMP context where contextEngineId == SnmpEngineId
    snmpContext = context.SnmpContext(self.snmpEngine)

    if criticalStatus:
      self.trap=temperatureCritical
    else:
      self.trap=temperatureOK
      
    # Create Notification Originator App instance.
    ntforg.NotificationOriginator.__init__(self,snmpContext)
    

  def dispatch(self):
    # Build and submit notification message to dispatcher
    self.sendNotification(
      self.snmpEngine,
      # Notification targets
      'sendShutdownTrap',
      # Trap OID (IGFAE-USC-MIB::temperatureCritical)
      self.trap.name,
      # ( (oid, value), ... )
      ( (self.roomTemp.name+(0,), rfc1902.Integer32(self.temperature)), )
    )
    # Run I/O dispatcher which would send pending message and process response
    self.snmpEngine.transportDispatcher.runDispatcher()
    


