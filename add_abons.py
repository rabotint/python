#!/usr/bin/env python
# -*- coding: utf-8 -*
import sys
import subprocess 
import socket
try:
	skript_command = sys.argv[1]
except:
	print "no given command"
	sys.exit()
if skript_command == "add":

	try:
		login = sys.argv[2]
	except:	
		print "no given login"
		sys.exit()

	try:
		net = sys.argv[3]
		sys.exit() if int(net) > 30 and int(net) < 24 else ""  
	except:
		print "no given netmask"
		sys.exit()
	try:
		SW_ip = sys.argv[4]
	except:	
		print "no given SW"
		sys.exit()

	try:
		VLAN = sys.argv[5]
		sys.exit() if int(VLAN) > 4094 and int(VLAN) < 0 else ""  
		
	except:	
		print "no given vlan"
		sys.exit()

	try:
		port = sys.argv[6]
	except:	
		print "no given port. The programm will continue without port number"
		port = "any free port"

elif skript_command == "dell":
	try:
		login = sys.argv[2]
	except:	
		print "no given login"
		sys.exit()
else:
	print "wrong command -T"
	sys.exit()

server = "router"
def get_free_netw(net):
	command = "/home/user/isp_ipplan_ipcalc.pl isp %s" %(net),
	command =  subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)  
	isp_net = command.stdout.read()
	return isp_net
def net_calk(isp_net):				 # make sure it is netmask or not 
	isp_ip_net_mask = isp_net.split("/")	  # separate ip and netmask /30 or /29 ... 
	ip_netw = isp_ip_net_mask[0].split(".")	# separete decimal digits in IP address
	ip_netw[3] = str((int(ip_netw[3])/(pow(2,32-int(isp_ip_net_mask[1]))))*pow(2,32-int(isp_ip_net_mask[1])))    # make sure that it is netmask
	ip_gw = ip_netw[:]			      # calculate gateway
	ip_gw[3] = str(int(ip_netw[3])  + 1 )
	ip_ab = ip_netw[:]			      # calculate IP
	ip_ab[3] = str(int(ip_netw[3])  + 2 )
	return (".".join(ip_netw),".".join(ip_gw),".".join(ip_ab)), isp_ip_net_mask[1]
def release_in_billing(command_release_abon):
	command_release_in_billing =  subprocess.Popen("sudo /jctl/bin/isp_login.pl", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	billing_error = command_release_in_billing.communicate(command_release_abon)
	command_release_in_billing.stdin.close()
	print u'abon released in billing' if billing_error[1] == "" else sys.exit("\033[1;31m" + "error in isp_login.pl" + "\033[1;m")
def release_in_user_conf(user_config_string):
#	subprocess.call("ssh router -T 'sudo cp /opt/netctl/etc/users.conf /opt/netctl/etc/users.conf.backup'")
	bash_command = """ssh router -T 'echo -e "%s" | sudo tee -a /opt/netctl/etc/users.conf'""" %(user_config_string)
	editing_user_conf = subprocess.call(bash_command, shell=True)
	print "user config is modified"
def route_file(QinQ,VLAN,GW,login):
	bash_command = "ssh router -T 'test -f /path/to/the/route/file/eth3.%s.%s' " %(QinQ,VLAN)
	rezult_bash = subprocess.call(bash_command, shell=True)
	existing_file = False if rezult_bash==1 else True 
	if existing_file:
		print "route file exist"
		route_file = subprocess.Popen("ssh router -T 'cat /path/to/the/route/file/eth3.%s.%s'"%(QinQ,VLAN),shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		route_file =  route_file.communicate()[0]
		route_number = route_file[route_file.rfind("eth3."):]
		try:	#check correct define number of route
			route_number = int(route_number[route_number.find(":")+1:route_number.find(" ")]) + 1
		except:
			print "\033[1;31m" + "The error occured in route file. Did not find the number of route alias." + "\033[1;m"
			sys.exit()		
		route_number = str(route_number)
		route_string = '#_%(login)s\neth3_%(qinq)s_%(vlan)s_a%(route_number)s="eth3.%(qinq)s.%(vlan)s:%(route_number)s %(gw)s broadcast +"' % {"qinq":QinQ,"vlan":VLAN,"login":login,"gw":GW,"route_number":route_number}
#		print route_string
		bash_command = """echo -e '%s' | sudo tee -a /path/to/the/route/file/eth3.%s.%s""" %(route_string,QinQ,VLAN)
		ssh_router_command(bash_command)
		subprocess.call("ssh router sudo /netctl/bin/netconf vup eth3.%s.%s:%s"%(QinQ,VLAN,route_number),shell=True)
	else:
		print "route file does not exist"
		route_string = 'eth3_%(qinq)s_%(vlan)s="eth3.%(qinq)s.%(vlan)s link eth3.%(qinq)s mtu 1500 group downlink type vlan id %(vlan)s"\n#_%(login)s\neth3_%(qinq)s_%(vlan)s_a0="eth3.%(qinq)s.%(vlan)s:0 %(gw)s broadcast +" ' % {"qinq":QinQ,"vlan":VLAN,"login":login,"gw":GW}
		command = """echo -e '%s' | sudo tee -a /path/to/the/route/file/eth3.%s.%s""" %(route_string,QinQ,VLAN)
		ssh_router_command(command)
		subprocess.call("ssh router -T sudo /netctl/bin/netconf vup eth3.%s.%s"%(QinQ,VLAN),shell=True)
		subprocess.call("ssh router -T sudo /netctl/bin/netconf vup eth3.%s.%s:0"%(QinQ,VLAN),shell=True)
		print "ssh router sudo /netctl/bin/netconf vup eth3.%s.%s"%(QinQ,VLAN)
		print "ssh router sudo /netctl/bin/netconf vup eth3.%s.%s:0"%(QinQ,VLAN)
def qinq_definition(SW_ip):
		bash_command="ssh btr ip ro get " + SW_ip
		ssh_route_definition = subprocess.Popen(bash_command,shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		ip_ro_get = ssh_route_definition.communicate()
		ssh_route_definition.stdin.close()
		ip_ro_split = ip_ro_get[0].split(" ")
		if ip_ro_split[1] == "dev":
			iface_name = ip_ro_split[2].split(".")
			qinq_num = int(iface_name[1])
		else:
			print " BAD switch IP "
			sys.exit()
		return qinq_num
			
def dell_user(login):
		usr_conf_str = ssh_router_command("sudo sed -n '/%s/,/^$/p' /opt/netctl/etc/users.conf"%(login))
		sys.exit() if usr_conf_str[1] <> None else ""
		usr_conf_str = usr_conf_str[0].split("\n")
		netw = []
		for i in usr_conf_str:  # monkeycode for deliting melicious char
			if i.find("<if ") <> -1 :
				iface = i.replace("<if ", "")
				iface = iface.replace(">", "")
				iface = iface.replace(" ", "")
				iface = iface.replace("\t", "")
				print iface     
			elif i.find("<net ") <> -1 :
				net = i.replace("<net ", "")
				net = net.replace(">", "")
				net = net.replace(" ", "")
				net = net.replace("\t", "")
				net = net.replace("\n", "")
				netw.append(net)
			else:
				continue    
		# delete user config string via sed 
		ssh_router_command("sudo sed -i '/%s/,/^$/d' /opt/netctl/etc/users.conf"%(login))
		# delete IP in billing via banjo server's skript
		for i in netw:
			command_release_in_billing =  subprocess.Popen("sudo /jctl/bin/isp_login.pl", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
			command_release_in_billing.communicate("%s gw default"%(i))
			command_release_in_billing.stdin.close()
			print u'network %s was deleted from billig database'%(i)
		# delete interface and route
		route_string = ssh_router_command('cat /path/to/the/route/file/%s'%(iface))
		route_string = route_string[0].split("\n")
		sys.exit("\033[1;31m" + 'route file does not exist' + "\033[1;m") if route_string[0] == "" else ""
		n = 1
		for i in route_string:
			if i.find(iface) <> -1:
#				print i
				for b in netw:
					GW = net_calk(b)[0][1]
					if i.find(GW) <> -1:
						iface_alias = i[i.find(iface):i.find(GW)]
						command = "sudo /netctl/bin/netconf vdown %s"%(iface_alias)
						ssh_router_command(command)	
						print "vdown %s"%(iface_alias)
						command = "sudo sed -i '/%s/d;/%s/d' /path/to/the/route/file/%s"%(iface_alias,login,iface)
						ssh_router_command(command)
						print "deleted strings = %s in route file"%(str(n))
						n = n + 1
					else:
						continue
			else:
				continue
			existing_vlan_alias = subprocess.call("ssh router -T grep -q -e '{0}:' /path/to/the/route/file/{0}".format(iface), shell=True,stdout=subprocess.PIPE, stdin=subprocess.PIPE)	
		if int(existing_vlan_alias) == 1:
			ssh_router_command("sudo /netctl/bin/netconf vdown %s"%(iface))
			print "iface %s was downed"%(iface)
			ssh_router_command("sudo rm /path/to/the/route/file/%s"%(iface))
			print "file /path/to/the/route/file/%s was deleted"%(iface)
		elif int(existing_vlan_alias) == 0:
			print "many users on this iface. Route was not deleted "


def ssh_router_command(command):
		ssh_router = subprocess.Popen("ssh router -T", shell=True,stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		router_communicate = ssh_router.communicate(command)
		ssh_router.stdin.close()
		return router_communicate
if skript_command == "add":
	isp_net = get_free_netw(net)
	QinQ = str(qinq_definition(SW_ip))			# calk QinQ int objekt
	calk_net = net_calk(isp_net)[:]			# array with abon's ip, gateway and netmask as / 
	NET = calk_net[0][0] +"/" + calk_net[1]			# netmask as 4 octets in decimal digits
	GW = calk_net[0][1] + "/" + calk_net[1]			# gateway in form of 4 octets in decimal digits
	command_release_abon = "%s %s %s\n" %(NET, login, server)	#data for the script
	user_config_string = "\n<user %s>\n\t<if eth3.%s.%s>\n\t<net %s>\n</user>" %(login, QinQ, VLAN, NET)	#data for the script
	release_in_billing(command_release_abon)
	release_in_user_conf(user_config_string)
	route_file(QinQ,VLAN,GW,login)
	try:
		switch_hostname = socket.gethostbyaddr(SW_ip)[0]
		switch_hostname = switch_hostname.replace('.sw.isp.local', '')
	except:
		switch_hostname = 'unknown'
	print "- login - " + login
	print " - ip - " + calk_net[0][2]
	print " - mask - " + calk_net[1]
	print " - GW - " + GW[0:-3]
	print " - router - " + server
	print " - QinQ - " + QinQ
	print " - Vlan - " + VLAN
	print " - sw ip - " + SW_ip
	print " - sw name - " + switch_hostname
	print " - port - " + port 
elif skript_command == "dell":
	dell_user(login ) 
