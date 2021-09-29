import subprocess
import requests
import os 
import json
import yaml
from . import *
from app.Methods.cscController import tenantDetails, reqInstDetails, randomCSCName, writeCloudInit, vim_auth, instCSC, serviceRetrieve, selectFlavor, NEWreqInstDetails, cscNetworkCreate, createChain, randomAppd
from app.Methods.manoConnector import *
import time
base_dir = os.path.dirname(os.path.dirname(__file__))
UPLOAD_FOLDER_DESC = os.path.join(os.sep, base_dir,'uploads')
import sys
#authfile='/home/meson/meson/Meson_Agent/app/meson_auth.conf'
authfile='/api/app/meson_auth.conf'
##convert the auth file to a handlable dictionary
auth_dict=mesonAuth_nonsilent(authfile)

#@uploads_dir='/home/meson/meson/Meson_Agent/uploads'
uploads_dir='/api/uploads'


def talk2SR(appD, role, *args):
	'''
	description: communicate appDs or appDCs to SR
	param: appD, CSC role, VimAccountID (optional)
	return: response data	
	'''
	provider_ep = 'http://SR:8081/appDR'
	consumer_ep1 = 'http://SR:8081/appDCService'
	consumer_ep2 = 'http://SR:8081/appDCUpdated'
	headers = {'Content-Type':'application/json'}
	if len(args) == 0:
		appD = json.dumps(appD)
		if role == "provider":
			return requests.post(provider_ep, headers=headers, data=appD)
		elif role == "consumer":
			return requests.post(consumer_ep1, headers=headers, data=appD)
		else:
			raise ValueError("No valid role. Role should be either 'provider' or 'consumer', not {0}".format(role))
	else: # phase: received best PoP from EPS. Convey enriched appDC to SR 
		appD['appDC']['PoPID'] = args 
		appD = json.dumps(appD)
		return requests.post(consumer_ep2, headers=headers,data=appD)

def forwardCandPoPs2EPS(appDs):
	'''
	description: Post a list of provider appDs to PoP Selection
	param: single json file of multiple appDs
	return: response data	
	'''
	# TODO: replace with the correct endpoint
	candidate_PoPs_ep = 'http://pop_selection:8080/epsm_api/pop_data'
	appDs = json.dumps(appDs)
	headers = {'Content-Type': 'application/json', 'Accept':'application/json'}
	response = requests.post(candidate_PoPs_ep, data=appDs,headers=headers)
	return response



def sendWeights(appDC):
	'''
	description: Post consumer KPIs to PoP Selection
	param: appDC
	return: response data
	'''
	# TODO: replace with the correct endpoint
	weights_EPS_ep = 'http://pop_selection:8080/epsm_api/consumer_requirements'
	post_data = appDC['appDC']['PoP_Preferences']
	post_data = json.dumps(post_data)
	headers = {'Content-Type': 'application/json', 'Accept':'application/json'}
	response = requests.post(weights_EPS_ep, data=post_data, headers=headers)
	# expected response is "Consumer's requirements assigned"
	return response


def talk2EPS(appDs, appDC):
	'''
	description: call the individual functions that talk to EPS end points
	param: single json file of multiple providing appDs, and the appDC
	return: response data	
	'''
	response1 = forwardCandPoPs2EPS(appDs)
	response2 = sendWeights(appDC)
	return response1, response2


def talk2OSM(nstD_file, vimaccid):
	'''
	Description: Code for interaction with the OSM via OSM Client scripts
	'''
	response1 = onboard_nst(nstD_file)
	response2 = inst_nst(nstD_file,vimaccid)
	return response1, response2


def messageForwarder(appD, nstD, role):   
	'''
	description: instruments the various communication functions, according to the MESON Architecture logic 
	param: an appD (can be either appD or appDC), a nstD, and a role (which has been previously retrieved from the appD type) 
	return: state message
	'''
	if role == 'provider':
		appd=appD
		vim_account_id = appD['appD']['PoPID']
		OSMresponse1, OSMresponse2 = talk2OSM(nstD, vim_account_id)
		if 'error' in OSMresponse1: 
			message = OSMresponse1
			return message
		elif 'error' in OSMresponse2:
			message = OSMresponse2
			return message
		SRresponse = talk2SR(appD, role)
		if SRresponse.json() == "appD has been successfully posted to SR":
			PoPID = appD["appD"]["PoPID"]
			message = 'Providing nstD has been uploaded to {}. The respective appD has been stored in Service Registry'.format(PoPID)
			return message
		else:
			#Show SR response in case of error
			message = SRresponse.json()
			#message = 'something went wrong with uploading the provider\'s appD to SR'
			return message
 
	if role == 'consumer':
		SRresponse = talk2SR(appD, role)
		print(str(SRresponse.content))
		if SRresponse.json() == []:
			message = 'no appDs that match with the appDC'
			return message
		elif SRresponse.status_code == 400:
			message = 'bad request posted to Service Registry'
			return message
		elif SRresponse.status_code == 500:
			message = 'the appD requested instantiation on a PoP that does not exist in the database'
			return message
		else: # SRdata is a list of provider appDs 

			EPSresponse1, EPSresponse2 = talk2EPS(SRresponse.json(), appD)
			if EPSresponse1.json == []:
				message = "PoP Selection returned an empty list"
				return message	
			elif EPSresponse1.status_code == 200 and EPSresponse2.status_code == 200:
				PoPID = EPSresponse1.json()['appD']['PoPID']
				vim_account_id = PoPID
				OSMresponse1, OSMresponse2 = talk2OSM(nstD, vim_account_id)
				if 'error' in OSMresponse1: 
					message = OSMresponse1
					return message
				elif 'error' in OSMresponse2:
					message = OSMresponse2
					return message 
				SRresponse = talk2SR(appD, role, PoPID)
				print('&&&&The EPS response 1 was: ' + str(EPSresponse1.content))
				#Possible options: openstack, icom, ntua
				if 'openstack' in str(EPSresponse1.content):
					selected_vim='VIM1'
				elif 'icom' in str(EPSresponse1.content):
					selected_vim='VIM2'
				elif 'ntua' in str(EPSresponse1.content):
					selected_vim='VIM3'
				else:
					print('No VIM matches known infrastructure, exiting...')
					sys.exit() 
				print('@---The selected VIM is: '+selected_vim+'---@')
				if SRresponse.status_code == 200:
					##############CSC FLOW##############
					appd=randomAppd()
					appdpath=str(uploads_dir+'/'+appd)
					with open(appdpath, "w") as f:
						yaml.dump(EPSresponse1.json(), f)
						f.close()
					appdc=appD
					server_name=str('csc_server_'+randomCSCName())
					#Retrieve the image name (service name) through querrying the SR
					image=serviceRetrieve(appd, appdc, uploads_dir)
					#Select flavor to be used depending on user requirements
					flavor=str(selectFlavor())
					waitForInst(auth_dict, nstD)
					#Create the cloud-init file
					writeCloudInit(appd, appdc, uploads_dir, auth_dict)
					#Generate the VIM authorization environment
					vim_auth(auth_dict, selected_vim)
					#Create the CSC network
					image='firewall'
					network_id=cscNetworkCreate()
					#Instantiate the CSC slices
					instCSC(appd, appdc, uploads_dir, flavor, image, server_name, auth_dict, network_id)
					#chain=createChain(appd, appdc, uploads_dir, network_id)
					message = 'The CSC slice is being instantiated'
					return message
				else:
					message = 'updated appDC was not conveyd to SR properly'
					return message
			# if the EPS ranking returns only 'bad' PoPs
			else:
				message = "PoP selection returned a bad response"	
				return message	
				# end of step 6 # 
