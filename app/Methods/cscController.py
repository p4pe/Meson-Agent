import yaml
from osmclient import client
from osmclient.common.exceptions import ClientException
import os
from prettytable import PrettyTable
import requests
from app.Methods.mesonAuthorization import*
#from mesonAuthorization import mesonAuth_nonsilent
import subprocess
import json
import time


#DEBUG START#
import sys
#DEBUG END#

#Clean the screen
#os.system('clear')

#The lines in this block hangle the export of the authorization data
##location of the configuration file
#authfile='/home/meson/meson/app/Meson_Agent/meson_auth.conf'

#authfile location in the container
authfile='/api/app/meson_auth.conf'
#uploads_dir='/home/meson/meson/Meson_Agent/uploads'
#uploads dir location in the container
uploads_dir='/api/uploads'

#function to get tenant details from the appd and appdc files
def tenantDetails(appd, appdc, uploads_dir):
   print('**tenantDetails function called**')
   prov_info=[]
   cons_info=[]
   #PROVIDER
   with open(uploads_dir+'/'+appd, 'r') as p:
      parse_prov=yaml.safe_load(p)
   #parse provider nsd_ref_name  
      nsd_ref=parse_prov['appD']['appServiceProduced']['nsd_ref_name']
      prov_info.append(nsd_ref)
   #parse provider member_vnf_index
      member_vnf=parse_prov['appD']['appServiceProduced']['member_vnf_index']
      prov_info.append(member_vnf)
   #parse provider popid
      prov_popid=parse_prov['appD']['PoPID']
      prov_info.append(prov_popid)

   #parse provider vnfd_name
      for object in parse_prov['appD']['appServiceProduced']['CSC_VNF']:
          prov_info.append(object["vnfdName"])
  #CONSUMER
   parse_cons=appdc
   #parse consumer nsd_ref_name
   nsd_ref=parse_cons['appDC']['appServiceRequired']['nsd_ref_name']
   cons_info.append(nsd_ref)
   #parse consumer member_vnf_index
   member_vnf_cons=parse_cons['appDC']['appServiceRequired']['member_vnf_index']
   cons_info.append(member_vnf_cons)
   return prov_info,cons_info


#function to get instantiation information for the csc slice from OSM
##calls the tenantDetails function
def reqInstDetails(appd, appdc, uploads_dir):
   print('**reqInstDetails function called**')
   csc_details=[]
   hostname = str(auth_dict['MANO']['hostname'])
   user = str(auth_dict['MANO']['user'])
   password = str(auth_dict['MANO']['password'])
   project = str(auth_dict['MANO']['project'])
   print('hostname is: '+hostname)
   print('user is: '+user)
   print('password is: '+password)
   print('project is: '+project)
   kwargs = {}
   if user is not None:
       kwargs['user']=user
   if password is not None:
       kwargs['password']=password
   if project is not None:
      kwargs['project']=project
   myclient = client.Client(host=hostname, sol005=True, **kwargs)
   prov_nsd=tenantDetails(appd,appdc,uploads_dir)[0][0]
   cons_nsd=tenantDetails(appd,appdc,uploads_dir)[1][0]
   resp_prov = myclient.ns.get(prov_nsd)
   resp_cons = myclient.ns.get(cons_nsd)
   responses=[ resp_prov, resp_cons ]

   #get specific info from the return of OSM above
   for r in responses:
      #find which vnf index comes first
      member_vnf_index=str(tenantDetails(appd,appdc,uploads_dir)[0][1]) #TODO same for the consumer
      vnfs=r['deploymentStatus']['vnfs']
      for vnf in vnfs:
         if vnf['member_vnf_index']==member_vnf_index:
            ip=vnf['vms'][0]['interfaces'][1]['ip_address']
            x=vnf['vms'][0]['interfaces'][1]['vim_info']
            x_splitted=x.split(',')
            break
      for item in x_splitted:
         if 'device_id' in item:
            device_id=item.split(' ')[2]
         if 'network_id' in item:
            uuid=item.split(' ')[2]   
      csc_details.append(ip)
      csc_details.append(device_id)
      csc_details.append(uuid)
   return csc_details

#this function generates a random filename for the appd file
def randomAppd():
   import random
   import string
   print('***randomAppd function called***')
   #get random string of letters and digits
   source = string.ascii_letters + string.digits
   result_str = ''.join((random.choice(source) for i in range(8)))
   return str(result_str)


#this function generates a randon CSC server name to avoid conflicts
def randomCSCName():
   import random
   import string
   print('**RandomCSCName function called**')
   #get random string of letters and digits
   source = string.ascii_letters + string.digits
   result_str = ''.join((random.choice(source) for i in range(8)))
   return str(result_str)

#creates a cloud_init file that will be sent to openstack with the instantiation parameters
##calls reqInstDetails
def writeCloudInit(appd, appdc, uploads_dir, auth_dict):
   print('**writeCloudInit function called**')
   print('Preparing Cloud-init...')
   csc_details=NEWreqInstDetails(appd,appdc,uploads_dir,auth_dict)
   print('--------------------------------------')
   print(csc_details)
   print(csc_details[0])
   print(csc_details[1])
   print(csc_details[2])
   print(csc_details[3])
   print('--------------------------------------')

   f = open('cloud_init', 'w')
   f.write('#!/bin/bash\n')
   f.write('IP1='+csc_details[0]+'\n')
   f.write('IP2='+csc_details[3]+'\n')
   f.write('iptables -t nat -A PREROUTING -s $IP1 -j DNAT --to-destination $IP2'+'\n')
   f.write('iptables -t nat -A PREROUTING -s $IP2 -j DNAT --to-destination $IP1'+'\n')
   f.write('iptables -t nat -A POSTROUTING -j MASQUERADE\n')
   f.write('sleep 3\n')
   f.write('echo 1 > /proc/sys/net/ipv4/ip_forward\n')
   f.write('sysctl -p\n')
   f.close()
   print('Cloud-init file built successfully!\n')



#this function uses the meson authorization contents to build an auth-source file for the vim
#NOTE: currently only works with Openstack and the default name is vim_auth.sh
def vim_auth(auth_dict, selected_vim):
   print('**vim_auth function called**')
   print('Creating VIM auth file...')
   v = open('vim_auth.sh', 'w')
   v.write('export OS_AUTH_URL='+str(auth_dict[selected_vim]['auth_url'])+'\n')
   v.write('export OS_IDENTITY_API_VERSION='+str(auth_dict[selected_vim]['api_id_version'])+'\n')
   v.write('export OS_PROJECT_NAME='+str(auth_dict[selected_vim]['project_name'])+'\n')
   v.write('export OS_USERNAME='+str(auth_dict[selected_vim]['username'])+'\n')
   v.write('export OS_USER_DOMAIN_NAME='+str(auth_dict[selected_vim]['user_dom_name'])+'\n')
   v.write('export OS_PROJECT_DOMAIN_ID='+str(auth_dict[selected_vim]['project_dom_id'])+'\n')
   v.write('export OS_PASSWORD='+str(auth_dict[selected_vim]['password'])+'\n')
   v.close()

#creates a csc instantiation batch file that uses the net ids (uuid) and
#-vm ids (device_id) and the pregenerated cloud-init file for the instantiation
# uses the file name vim_auth.sh by default
def instCSC(appd, appdc, uploads_dir, flavor, image, server_name, auth_dict, network_id):
   print('**instCSC function called**')
   print('Building CSC Instantiation sequence...')
   csc_details=NEWreqInstDetails(appd,appdc,uploads_dir,auth_dict)
   f = open('inst_commands', 'w')
   f.write('openstack server create --flavor '+str(flavor)+'  --image '+str(image))
   f.close()
   f = open('inst_commands', 'a')
   f.write(' \\\n--nic net-id='+str(csc_details[2])+' --hint same_host='+str(csc_details[1]))
   f.write(' \\\n--nic net-id='+str(csc_details[5])+' --hint same_host='+str(csc_details[4]))
#   f.write(' \\\n--nic net-id='+str(network_id))
   f.write(' \\\n--nic net-id='+str(network_id)+',v4-fixed-ip='+'192.168.200.3')
   f.write(' --user-data cloud_init '+str(server_name))
   f.close()
   print('Command Written - ready to execute!')
   print('CSC VNF is being instantiated! Congratulations!')
   #instantiate csc slice
   os.system("chmod +x inst_commands")
   #source the VIM credentials and run the instantiation command
   vim_auth='source vim_auth.sh'
   #inst_commands='echo "The auth url is: $OS_AUTH_URL"'
   inst_comm='./inst_commands'
   commands_list = [ vim_auth , inst_comm ]
   commands_string=str(' ; '.join(commands_list))
   print('the list of all commands in series is: '+commands_string)
   proc=subprocess.Popen(commands_string, shell=True, executable='/bin/bash')
   #proper cleanup, kill the child process and finish communication"
   try:
      outs, errs = proc.communicate(timeout=15)
   except TimeoutExpired:
      proc.kill()
      outs, errs = proc.communicate()


def serviceRetrieve(appd, appdc, uploads_dir):
   print('**serviceRetrieve function called**')
   VIM=tenantDetails(appd,appdc,uploads_dir)[0][2]
   vnfds=tenantDetails(appd,appdc,uploads_dir)[0][3:]
   vnfd_name=vnfds
   print('***ALL OF TENANT DETAILS***')
   headers = {'Content-Type': 'application/json'}
   data = { "PoPID": VIM , "vnfd_names": vnfd_name }
   print('DATA IS: '+str(data))
   #convert data to JSON as required by the SR endpoint
   jsondata = json.dumps(data)
   #print(data)
   response = requests.post('http://SR:8081/CSC', headers=headers, data=jsondata)
   Response=response.json()
   print('The answer from the SR was: ' +str(Response))
   return Response


#TODO: slect flavor intelligently
def selectFlavor():
   print('**selectFlavor function called**')
   flavor='m1.medium'
   return flavor


#############################################

def NEWreqInstDetails(appd, appdc, uploads_dir, auth_dict):
   time.sleep(45)
   print('**NEWreqInstDetails function called**')
   csc_details=[]
   hostname = str(auth_dict['MANO']['hostname'])
   user = str(auth_dict['MANO']['user'])
   password = str(auth_dict['MANO']['password'])
   project = str(auth_dict['MANO']['project'])
   kwargs = {}
   if user is not None:
       kwargs['user']=user
   if password is not None:
       kwargs['password']=password
   if project is not None:
      kwargs['project']=project
   myclient = client.Client(host=hostname, sol005=True, **kwargs)
   #the name of the service is an argument for the function
   #get all info for the provider and consumer nsds
   prov_nsd=tenantDetails(appd,appdc,uploads_dir)[0][0]
   cons_nsd=tenantDetails(appd,appdc,uploads_dir)[1][0]
   resp_prov = myclient.ns.get(prov_nsd)
   resp_cons = myclient.ns.get(cons_nsd)
   responses=[ resp_prov, resp_cons ]

   #get specific info from the return of OSM above
   for r in responses:
      for i in range(2):
         #find which vnf index comes first
         member_vnf_index=str(tenantDetails(appd,appdc,uploads_dir)[i][1])
         vnfs=r['deploymentStatus']['vnfs']
         for vnf in vnfs:
            if vnf['member_vnf_index']==member_vnf_index:
               ip=vnf['vms'][0]['interfaces'][1]['ip_address']
               x=str(vnf['vms'][0]['interfaces'][1]['vim_info'])
               x_splitted=x.split(',')
               break
         for item in x_splitted:
            if 'device_id' in item:
               device_id=item.split(' ')[2]
            if 'network_id' in item:
               uuid=item.split(' ')[2]
      csc_details.append(ip)
      csc_details.append(device_id)
      csc_details.append(uuid)
   return csc_details


def cscNetworkCreate():
   print('**cscNetworkCreate function called**')

   #Create the network in the VIM
   print('Create the CSC network in the VIM')
   netName = "csc-net1"
   f = open('netCreation', 'w')
   #f.write('netName=' +netName+ '\n')
   f.write("openstack network create " +netName+ '\n')
   f.close()

   #Crete the subnet for the CSC network in the VIM
   print('Create the CSC subnet in the VIM')
   subnetName = str(netName+"_subnet")
   baseIP = "192.168.200."
   subnet = "0/24"
   sn = open('subnetCreation' , 'w')
   sn.write('subnetName='+subnetName+'\n')
   sn.write("openstack subnet create "+subnetName + " --subnet-range "+baseIP+subnet+" --network "+netName)
   sn.close()

   print('Command Written - ready to execute')
   print('CSC network is being created!')
   os.system("chmod +x netCreation")
   os.system("chmod +x subnetCreation")
   vim_auth='source vim_auth.sh'
   netcr='./netCreation'
   snetcr='./subnetCreation'
   commands_list = [ vim_auth , netcr, snetcr ]
   commands_string=str(' ; '.join(commands_list))
   print('the list of all commands in series is: '+commands_string)
   proc=subprocess.Popen(commands_string, shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
   try:
      outs, errs = proc.communicate(timeout=30)
   except subprocess.TimeoutExpired:
      proc.kill()
      outs, errs = proc.communicate()
   time.sleep(5)
   #Process the netname into a string
   netname=outs
   network_id = [line for line in netname.split('\n') if "network_id" in line]
   network_id = str(network_id)
   print('The original network id is: '+network_id)
   network_id = network_id.split("|")[2]
   print('after split it is: '+network_id)
   network_id = str(network_id).strip(" ")
   print('The detected VIM CSC network id is: '+network_id)
   return network_id


def createChain(appd, appdc, uploads_dir, network_id):
   chain = serviceRetrieve(appd, appdc, uploads_dir)
   print("++++++++++chain+++++++++++")
   print(chain)
   image = chain
   baseIP="192.168.200."
   i = 0
   for service in image:
      i+=1
      print("++++++++++++++++++++++++++++++++++++++++++++++")
      serverName = service+"_"+str(i)
      sfc = open('sfcCreation', 'w')
      sfc.write("openstack server create " "--flavor " "m1.medium "  "--image " + str(service) + " --nic net-id=" + network_id + ",")
      sfc.write("v4-fixed-ip=" + baseIP + str(i + 3) + " "+ str(serverName))
      sfc.close()
      print('Command Written - ready to execute!')
      print('CSC Slice is being instantiated! Congratulations!')
        # instantiate csc slice
      os.system("chmod +x sfcCreation")
        # source the VIM credentials and run the instantiation command
      vim_auth = 'source vim_auth.sh'
        # inst_commands='echo "The auth url is: $OS_AUTH_URL"'
      inst_comm = './sfcCreation'
      commands_list = [vim_auth, inst_comm]
      commands_string = str(' ; '.join(commands_list))
      print('the list of all commands in series is: ' + commands_string)
      proc = subprocess.Popen(commands_string, shell=True, executable='/bin/bash')
      try:
          outs, errs = proc.communicate(timeout=15)
      except TimeoutExpired:
          proc.kill()
          outs, errs = proc.communicate()

