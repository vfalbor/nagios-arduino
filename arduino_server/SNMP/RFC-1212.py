# Imported just in case new ASN.1 types would be created
from pyasn1.type import constraint, namedval
from pysnmp.proto import rfc1155

# Imports

( Integer, ObjectIdentifier, OctetString, ) = mibBuilder.importSymbols("ASN1", "Integer", "ObjectIdentifier", "OctetString")
#( ObjectName, ) = mibBuilder.importSymbols("RFC1155", "ObjectName")
ObjectName = rfc1155.ObjectName()
( Bits, Integer32, MibIdentifier, TimeTicks, ) = mibBuilder.importSymbols("SNMPv2-SMI", "Bits", "Integer32", "MibIdentifier", "TimeTicks")

( MibIdentifier,
  MibScalar, 
  MibTableColumn,
  MibTableRow,
  MibTable ) = mibBuilder.importSymbols(   
    'SNMPv2-SMI',
    'MibIdentifier',
    'MibScalar',
    'MibTableColumn',
    'MibTableRow',
    'MibTable',
    )

# Exports

mibBuilder.exportSymbols(
    'RFC-1212',
    MibIdentifier=MibIdentifier,
    MibScalar=MibScalar,
    MibTableColumn=MibTableColumn,
    MibTableRow=MibTableRow,
    MibTable=MibTable
    )
