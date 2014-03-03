#!/usr/bin/perl
use strict;
use Getopt::Std;
use Log::Log4perl;
use Net::SNMP qw(:asn1);

Log::Log4perl::init('/etc/snmp/snmplog.conf');

sub process_trap($) {
    use NetSNMP::OID;    
    my ( $log ) = @_;
    # process the trap:
    
    $log->debug("VARIABLES:");

    my $maxlen = 0;
    my %data=qw();
    while(<STDIN>) {
        my ($oid, $value) = /([^\s]+)\s+(.*)/;
        $log->debug("  $oid: $value");
        $data{$oid}=$value;
    }

    $log->debug("HASH: ".join(", ",%data));
    $log->debug("KEYS: ".join(", ",keys %data));
    $log->debug("\n");

    #This extracts the values of the standard trap variables

    my $oid=NetSNMP::OID->new("$data{'SNMPv2-MIB::snmpTrapEnterprise.0'}");
    my %trap=(
	Origin     => $data{'SNMP-COMMUNITY-MIB::snmpTrapAddress.0'},
	OID        => $data{'SNMPv2-MIB::snmpTrapOID.0'},
	Community  => $data{'SNMP-COMMUNITY-MIB::snmpTrapCommunity.0'},
	Enterprise => "$SNMP::MIB{$oid}{moduleID}::$SNMP::MIB{$oid}{label}",
	Time       => $data{'DISMAN-EVENT-MIB::sysUpTimeInstance'},
	TrapNumber => $SNMP::MIB{$data{'SNMPv2-MIB::snmpTrapOID.0'}}{subID},
	);

    $log->debug("\%trap HASH: ".join(", ", %trap));

    my $entry;
    foreach $entry ('SNMP-COMMUNITY-MIB::snmpTrapAddress.0', 
		    'SNMP-COMMUNITY-MIB::snmpTrapCommunity.0',
		    'SNMPv2-MIB::snmpTrapOID.0', 
		    'SNMPv2-MIB::snmpTrapEnterprise.0',
		    'DISMAN-EVENT-MIB::sysUpTimeInstance') {
	delete $data{$entry};
    }

    $log->debug("KEYS: ".join(", ",keys %data));

    my @vars=qw();

    foreach (keys %data) {
	$oid=NetSNMP::OID->new("$_");
	my $oidArray='.'.join('.',$oid->to_array);
	$log->debug("oid: $oid");
        $log->debug("key: $_\n");
        $log->debug("\t\t$oidArray\n");
        $log->debug("\t\t$SNMP::MIB{$oidArray}{type}\n");
        $log->debug("\t\t$data{$_}\n");
	push(@vars, $oidArray);
	push(@vars, &{\&{$SNMP::MIB{$oidArray}{type}}}());
	push(@vars, $data{$_});	
    }

    $log->debug("\@var Contents: ".join(", ", @vars));

    return (\%trap, \@vars);
}

sub send_trap {
    my ($log, $trap, $vars, $snmp_target) = @_;

    $log->debug("SEND_TRAP: trap data:\n");
    foreach (keys %$trap) {
	$log->debug("\t\t  $_: $trap->{$_}");
    }
    $log->debug("SEND_TRAP: vars contents:\t  ". join('::',@$vars));
    $log->debug("SEND_TRAP: SNMP target:\t$snmp_target");

    my ($sess, $err) = Net::SNMP->session(
                                          -hostname  => $snmp_target,
                                          -port => 162,
                                          -community => $trap->{Community},
                                          -version => 1, #trap() requires v1
                                          );
    $log->debug("SEND_TRAP: session created");

    if (!defined $sess) {
        $log->debug("Error connecting to target $snmp_target: $err");
        return (1,$err);
    } else {
        $log->debug("SEND_TRAP: Sending trap...");
        my $enterprise=$SNMP::MIB{$trap->{Enterprise}}{objectID};
        my $result = $sess->trap(
                                 -agentaddr => $trap->{Origin},
                                 -varbindlist => $vars,
                                 -enterprise => $enterprise,
                                 -specifictrap => $trap->{TrapNumber},
                                 );
        return ($result,$sess->error());
    }

}

my $log = Log::Log4perl->get_logger("UPS");

my $hostname = <STDIN>;
chomp($hostname);
my $ipaddress = <STDIN>;
chomp($ipaddress);

my ($trapParams, $trapVars)=process_trap($log);

$log->debug("hostname:\t$hostname");
$log->debug("IP address:\t$ipaddress");
$log->debug("trap contents:\n");
foreach (keys %$trapParams) {
    $log->debug("\t  $_: $trapParams->{$_}");
}
$log->debug("vars contents:\t  ". join('::',@$trapVars));

my $cmd='';

my $ip;
for ($ip=37;$ip<=157;$ip++) {
    if ( $ip==41 || $ip==68 || $ip==86 || $ip==110 || $ip==157 ) {
        next;
    }

    my ($res, $error)=send_trap($log, $trapParams, $trapVars, '172.16.58.'.$ip);

    if (! $res ){
        $log->error("An error occurred sending the trap: $error");
    } else {
        $log->debug("Trap sent successfully");
    }

}


for ($ip=239;$ip<=246;$ip++) {
    if ( $ip==41 || $ip==68 || $ip==86 || $ip==110 || $ip==157 ) {
        next;
    }

    my ($res,$error)=send_trap($log, $trapParams, $trapVars, '172.16.58.'.$ip);

    if (! $res ){
        $log->error("An error occurred sending the trap: $error");
    } else {
        $log->debug("Trap sent successfully");
    }

}

if ($trapParams->{Enterprise}=~/MG-SNMP-UPS-MIB::upsmgTraps/) {
    if ($trapParams->{TrapNumber}==5) {
	$cmd='shutdown -h now';
    }
} elsif ($trapParams->{Enterprise}=~/USC-IGFAE-MIB::traps/) {
    if ($trapParams->{TrapNumber}==3) {
	$cmd='shutdown -h now';
    }
    
}

if ( $cmd ) {
    $log->debug("Command to execute: $cmd");
    exec($cmd);
}
