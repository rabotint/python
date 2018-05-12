#!/usr/bin/env python
# -*- coding: utf-8 -*-


from pysnmp.hlapi import *
import sys
import subprocess
import socket
# DATA
# oids for gpon
vlan_oid = '1.3.6.1.4.1.2011.5.14.5.2.1.25'
qinq_oid = '1.3.6.1.4.1.2011.5.14.5.2.1.6'
port_oid = "1.3.6.1.4.1.2011.5.14.5.2.1.0"

#This object indicates the reason why the ONT went offline.
#Options:
last_down_cause_errors={\
	0:" - The cause of ONT's down is that the ont is deleted",\
	1:" - The cause of ONT's down is that the ont is disconnected",\
	2:" - The cause of ONT's down is that the ont is losi(OLT can not receive\
	   expected optical signals from ONT)",\
	3:" - The cause of ONT's down is that the ont is lofi(OLT can not receive\
	   expected optical frame from ONT)",\
	4:" - The cause of ONT's down is that the ont is sfi(Signal fail of ONUi)",\
	5:" - The cause of ONT's down is that the ont is loai(Loss of acknowledge with ONUi)",\
	6:" - The cause of ONT's down is that the ont is loami(Loss of PLOAM for ONUi)",\
	7:" - The cause of ONT's down is that the ont fails to be deactivated",\
	8:" - The cause of ONT's down is that the ont is deactivated",\
	9:" - The cause of ONT's down is that the ont is reseted",\
	10:" - The cause of ONT's down is that the ont is registered again",\
	11:" - The cause of ONT's down is that the ont popup test fails",\
	12:" - The cause of ONT's down is that the ont authentication fails",\
	13:" - The cause of ONT's down is that the ont is powered off",\
	14:" - Reserved",\
	15:" - The cause of ONT's down is that the ont is loki(Loss of key synch with ONUi)",\
	16:" - The cause of ONT's down is that the ont is noerror",\
	17:" - Indicates that the query fails or no information is detected"\
	}



# vars
try:
    login = sys.argv[1]
except:
    print "ERROR: No argument login given"
    exit()


def get_qinq_vlan (login):
	command = subprocess.Popen("sed -n '/"+ login +"/{n;p;}' /puth/to/user/conf/*", shell=True,stdout=subprocess.PIPE, stdin=subprocess.PIPE)
	usr_cfg_str = command.communicate()
	command.stdin.close()
	sys.exit("Wrong login") if usr_cfg_str[0] == "" else ""
	usr_cfg_str = usr_cfg_str[0].replace(">\n", "")
	usr_cfg_str = usr_cfg_str.split(".")
	vlan = usr_cfg_str[-1]
	qinq = usr_cfg_str[-2]
	return vlan, qinq

def get_snmp_next(ip,oid,compare=False):
	find = {}
	for (errorIndication,
	     errorStatus,
	     errorIndex,
	     varBinds) in nextCmd(SnmpEngine(),
				  CommunityData('public'),
				  UdpTransportTarget((ip, 161), timeout=5.0, retries=2),
				  ContextData(),
				  ObjectType(ObjectIdentity(oid)),
				  lookupMib=False, lexicographicMode=False):

	    if errorIndication:
		print(errorIndication)
		break
	    elif errorStatus:
		print('%s at %s' % (errorStatus.prettyPrint(),
				    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
		break
	    elif compare <> False:
#		d = {str(varBind[0]).split(".")[-1]:int(varBind[1]) for varBind in varBinds if str(varBind[1]) == compare}
		d = {str(varBind[0]).split(".")[-1]:str(varBind[1]) for varBind in varBinds if str(varBind[1]) == compare}
		find.update(d)	
#	print find
	return find

def get_req(ip,oid):
	errorIndication, errorStatus, errorIndex, varBinds = next(
		getCmd(SnmpEngine(),
			CommunityData("public"),
			UdpTransportTarget(
			(ip, 161), timeout=5.0, retries=2
			),
			ContextData(),
			ObjectType(ObjectIdentity(oid)),
			lookupMib=False, lexicographicMode=False)
	)
#	print varBinds
	return varBinds[0][1]


# difine qinq and vlan
qinq_vlan = get_qinq_vlan(login)
vlan = qinq_vlan[0]
qinq = qinq_vlan[1]




for new_ip in ["10.10.11.32","10.10.11.33","10.10.11.35"]:
	find_vlans = get_snmp_next(new_ip,vlan_oid,vlan)
	find_qinq = get_snmp_next(new_ip,qinq_oid,qinq)
	for item in find_vlans:
		if find_qinq.get(item) <> None:
			service_port = item
			break
		else:
			continue
	if "service_port" in locals():
		ip = new_ip
		break
else:
	sys.exit("abon don't found on gpon")
host = socket.gethostbyaddr(ip)[0]
print host.replace(".l2.skif.com.ua","")
# get slot / frame / port /ont id
port_id = []
for i in range(2,6):
	port_oid_num = port_oid.split(".")
	port_oid_num[-1] = str(i)
	port_oid_num.append(service_port)
	port_id.append(get_req(ip,".".join(port_oid_num)))
	
# probably if_number depends on port / slot and hex nuber. I could find it from get request, 
# but i think by mathematik operations it will be work more quickly
# "0b1111101" + "0000" + "frame" + "0" + "slot" + "0" + "port" + "00000000"
gpon = "GPON " + str(port_id[0]) + "/" + str(port_id[1]) + "/" + str(port_id[2])
if_id = get_snmp_next(ip,"1.3.6.1.2.1.31.1.1.1.1",gpon)
if_id = if_id.keys()[0]
ont = str(port_id[3] )
print gpon +  "   ont =  " + ont
# ont description
ont_desc = "1.3.6.1.4.1.2011.6.128.1.1.2.43.1.9" +"."+if_id+"."+ont
print "ont description is -  " + get_req(ip,ont_desc)
# last down issue
last_down_cause_errors_mib = "1.3.6.1.4.1.2011.6.128.1.1.2.101.1.8" + "." + if_id +  "." + ont + ".0"
last_down_cause = get_req(ip,last_down_cause_errors_mib)
print last_down_cause_errors.get(last_down_cause)
onu_status_mib = "1.3.6.1.4.1.2011.6.128.1.1.2.62.1.22"+"."+if_id+"."+ont+".1"
onu_status = get_req(ip,onu_status_mib)
if onu_status == 1:
	print "ont online"
elif onu_status == 2:
	print "ont ofline"
	sys.exit()
else:
	print onu_status_mib 
	print onu_status
	sys.exit()
ont_distace_mib = "1.3.6.1.4.1.2011.6.128.1.1.2.46.1.20" + "." + if_id + "." + ont
ont_distance = get_req(ip,ont_distace_mib) 
if ont_distance == -1:
	print "failed test"
else:
	print "ont distance = " +  str(ont_distance)
	
#ont_uptime = get_req(ip,ont_uptime_mib)
#print type(ont_uptime)
#ont_uptime.prettyPrin()
ont_temper_mib = "1.3.6.1.4.1.2011.6.128.1.1.2.51.1.1" + "." + if_id + "." + ont
ont_temper = get_req(ip,ont_temper_mib)
if ont_temper == 2147483647:
	print "temperature test fail"
else:
	print "The temperature of the optical module, unit C : " + str(ont_temper)
ont_current_mib = "1.3.6.1.4.1.2011.6.128.1.1.2.51.1.2" + "." + if_id + "." + ont
ont_current = get_req(ip,ont_current_mib)

if ont_current == 2147483647:
	print "current false"
else:
	print "The Bias Current of the optical module, unit mA. : " + str(ont_current)
ont_power_tx_mib = "1.3.6.1.4.1.2011.6.128.1.1.2.51.1.4" + "." + if_id + "." + ont
ont_power_tx = get_req(ip,ont_power_tx_mib)
if ont_power_tx == 2147483647:
	print "power tx false"
else:
	print "Rx optical power(dBm), unit 1dBm. " + str(ont_power_tx/100.0)
ont_power_rx_mib = "1.3.6.1.4.1.2011.6.128.1.1.2.51.1.6" + "." + if_id + "." + ont
ont_power_rx = get_req(ip,ont_power_rx_mib)
if ont_power_rx == 2147483647:
	print "power rx false"
else:
	print "OLT Rx ONT optical power(dBm), unit 1dBm. " + str((ont_power_rx/100.0)-100)

ont_voltage_mib = "1.3.6.1.4.1.2011.6.128.1.1.2.51.1.5" + "." + if_id + "." + ont
ont_voltage = get_req(ip,ont_voltage_mib)
if ont_voltage == 2147483647:
	print "voltage definition is false"
else:
	print "The power feed voltage of the optical module, unit V. " + str(ont_voltage/100.0)

ont_mac_mib = "1.3.6.1.4.1.2011.6.128.1.1.2.46.1.21" + "." + if_id + "." + ont

ont_mac = get_req(ip,ont_mac_mib)
if ont_mac == -1:
	print "mac definition error"
else:
	print "The number of MAC addresses that are learned by the ONT =  " + str(ont_mac)


