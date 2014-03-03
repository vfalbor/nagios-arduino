from re import compile
from locale import atof

def S_ERROR( messageString = '' ):
  return { 'OK' : False, 'Message' : str( messageString )  }

def S_OK( value = '' ):
  return { 'OK' : True, 'Value' : value }

class Sensor(object):
    def __init__(self,host,service,time):
        self.__time=time
        self.__host=host
        self.__service=service
        self.__commandFile='/var/nagios/rw/nagios.cmd'
        self.__external=False

    def reset(self):
        self._error=0
        self._warn=0
        self._run=False
        self._perfdata=''
        self._exitCode=3

    def readSensor(self, *kargs):
        raise Exception( "This function MUST be overloaded!!" )

    def setExternal(self):
        self.__external=True

    def setHost(self,host):
        self.__host=host

    def setService(self,service):
        self.__service=service
        
    def unsetExternal(self):
        self.__external=False
    
    def process(self):
        raise Exception( "This function MUST be overloaded!!" )
    
    def processParameters(self,*strings):
        testArgs=compile(r'(\d+):(\d+)')
        errorString="%s limits: The lower limit must be " + \
                     "smaller than the higher limit"
        exceptString="%s parameter format must be of de form 'temp:temp'"

        try:
            temps=testArgs.search(strings[0]).groups()
            self._lowCritical=atof(temps[0])
            self._highCritical=atof(temps[1])
            if self._lowCritical > self._highCritical:
                return S_ERROR(errorString % "Critical")
        except:
            return S_ERROR(exceptString % "Critical")
        try:
            temps=testArgs.search(strings[1]).groups()
            self._lowWarning=atof(temps[0])
            self._highWarning=atof(temps[1])
            if self._lowWarning > self._highWarning:
                return S_ERROR(errorString % "Warning")
        except:
            return S_ERROR(exceptString % "Warning")

        return S_OK()

    
    def getOutputString(self):
        if self._perfdata:
            return '%s|%s' % ( self._outputString, self._perfdata )
        return self._outputString
    
    def getExitCode(self):
        return self._exitCode

    def getPerfData(self):
        return self._perfdata

    def submitExternalCommand(self):
        from os import system
        cmdStr=r'[%s] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%s;%s\n'
        if self.__external:
            outputStr='%s|%s' % (self._outputString,self._perfdata)
            externalCommand=cmdStr % (self.__time, self.__host,
                                      self.__service, self._exitCode,
                                      outputStr)
            cmd= "echo '%s' >> %s" % (externalCommand,self.__commandFile)
            system(cmd)
            
