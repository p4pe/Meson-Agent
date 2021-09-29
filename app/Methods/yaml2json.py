import yaml
import json
import os

def convert2json(myfile, uploads_dir):
	'''
	:description: Converts myfile to json-like, and returns it
	:params: myfile, directory
	:return: json-like file 
	'''

	if not isinstance(myfile, str):
		raise ValueError("convert2json only accepts strings, got {0}".format(type(myfile)))

	file_dir = os.path.join(os.sep,uploads_dir,myfile)

	only_name_file = os.path.splitext(myfile)[0]

	json_file_dir = os.path.join(os.sep,uploads_dir,only_name_file+'.json')

	if not os.path.isfile(file_dir) or not os.path.exists(file_dir):
		# return False if myfile is either directory, or a file that does not exist
		return False

	with open(file_dir, 'r') as yaml_in, open(json_file_dir, "w") as json_out:
		# yaml_object will be a list or a dict
		try:
			json_like_yaml = yaml.safe_load(yaml_in)	
			json.dump(json_like_yaml,json_out)	
		except yaml.YAMLError:
			return False
	return json_like_yaml
