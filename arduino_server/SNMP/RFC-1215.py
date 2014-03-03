
NotificationType, = mibBuilder.importSymbols('SNMPv2-SMI', 'NotificationType')

mibBuilder.exportSymbols(
    'RFC-1215',
    NotificationType=NotificationType,  # smidump always uses NotificationType
    TrapType=NotificationType    
    )

