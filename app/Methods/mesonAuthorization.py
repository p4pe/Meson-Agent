import yaml
from os import path

#does not work when imported as a module
#authfile='/home/meson/meson/Meson_Agent/meson_auth.conf'

#The functions below parse the authentication files MESON uses for the MANO and the respective VIMs
#import it in another script using 'from mesonAuthorization import mesonAuth, mesonAuth_nonsilent'
#non-silent version, prints to stdout, used for debugging
def mesonAuth_nonsilent(authfile):
   
   #TODO: assert type(authfile)==os.is.path
   auth_dict=[]
   if path.exists(authfile):
      #print('File exists')
      print('Detected auth file at: '+authfile)
      with open(authfile, 'r') as auth:
         try:
            auth_dict = yaml.safe_load(auth)
         except:
           print('Error trying to load the config file in YAML format')
           raise
      auth.close
   else:
      print('Authorization file does not exist in the specified path\n')
   print('Authorization file loaded')
   return auth_dict

#silent version, does not print to stdout in case of no error, only returns the auth_dict
#def mesonAuth(authfile):
 #  if path.exists(authfile):
 #     with open(authfile, 'r') as auth:
  #       try:
   #         auth_dict = yaml.safe_load(auth)
    #     except:
     #      print('Error trying to load the config file in YAML format')
      #     raise
      #auth.close
   #else:
    #  print('Authorization file does not exist in the specified path\n')
   #return auth_dict

###DEBUG RUN ME: auth_dict=mesonAuth(authfile)
