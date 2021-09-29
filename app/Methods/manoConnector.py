from osmclient import client
from osmclient.common.exceptions import ClientException
import yaml
from prettytable import PrettyTable
import os
import sys
#@from app.Methods.mesonAuthorization import *
#import app.Methods.mesonAuthorization
import time
##location of the configuration file
#authfile='/home/meson/meson/Meson_Agent/app/meson_auth.conf'
authfile='/api/app/meson_auth.conf'
##convert the auth file to a handlable dictionary
from app.Methods.mesonAuthorization import mesonAuth_nonsilent
auth_dict=mesonAuth_nonsilent(authfile)

#use a dedicated function to store mano connection details?
def connect2mano(filename):
    pass

def get_nst_id(descriptor):
    #nst_file = yaml.safe_load(descriptor)
    with open(descriptor, 'r') as desc:
        nst_file=yaml.safe_load(desc)
       #nst_file = yaml.safe_load(descriptor)
    nst_id = nst_file["nst"][0]["id"]
    return str(nst_id)

def onboard_nst(descriptor):
    #Mano connection details adjust to runtime environment
    hostname = str(auth_dict['MANO']['hostname'])
    user = str(auth_dict['MANO']['user'])
    password = str(auth_dict['MANO']['password'])
    project = str(auth_dict['MANO']['project'])
    kwargs = {}
    #Input verification
    if user is not None:
        kwargs['user'] = user
    if password is not None:
        kwargs['password'] = password
    if project is not None:
        kwargs['project'] = project
    #Connect & upload NST to OSM
    x=yaml.safe_load(descriptor)
    try:
        myclient = client.Client(host=hostname, sol005=True, **kwargs)
        OSMresponse = myclient.nst.create(x)
        return str(OSMresponse)
    except ClientException as e:
        return 'Error: ' + str(e)
        return OSMresponse
    except ClientException as e:
        return str(e)


def inst_nst(descriptor, vimaccid):
    # Mano connection details adjust to runtime environment
    hostname = str(auth_dict['MANO']['hostname'])
    user = str(auth_dict['MANO']['user'])
    password = str(auth_dict['MANO']['password'])
    project = str(auth_dict['MANO']['project'])
    kwargs = {}
    #vim domain
    vim_name = vimaccid
    nst_id = get_nst_id(descriptor)
    nst_name = nst_id # this could be anything, for convenience we use the same name
    # Input verification
    if user is not None:
        kwargs['user'] = user
    if password is not None:
        kwargs['password'] = password
    if project is not None:
        kwargs['project'] = project
    # Connect to OSM and instantiate
    try:
        myclient = client.Client(host=hostname, sol005=True, **kwargs)
        OSMresponse = myclient.nsi.create(nst_id, nst_name, vim_name)
        return str(OSMresponse)
    except ClientException as e:
      return 'Error: ' + str(e)
      return OSMresponse
    except ClientException as e:
      return str(e)


def waitForInst(auth_dict, descriptor):
   print("The waitForInst function is called...")
   id=get_nst_id(descriptor)
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

   flag = False
   while not flag:
      time.sleep(1)
      resp = myclient.nsi.get(id)
      status=resp['operational-status']
      if status == "running":
         flag = True
   print(status)
