from cerberus import Validator
import yaml
import os
from app.schemas.appDschema import ProvSchema, ConsSchema

def fileValidator(filename, uploads_dir):
	accept_input = True
	try:
		with open(os.path.join(os.sep,uploads_dir,filename), 'r') as f:
			try:
				x = yaml.safe_load(f)
			except (yaml.YAMLError, IOError, UnicodeDecodeError, TypeError):
				accept_input = False
			return accept_input
	except (FileNotFoundError, TypeError):
		accept_input = False
		return accept_input

#Testing WIP
def yamlValidator(file, uploads_dir):
	with open(os.path.join(os.sep,uploads_dir,file), 'r') as f:
		try:
			x = yaml.safe_load(f)
			if "appServiceProduced" in str(x):
				v = Validator()
				flag = v.validate(x, ProvSchema)
				errors = v.errors
				return flag, errors, 'provider'
			elif "appServiceRequired" in str(x):
				v = Validator()
				flag = v.validate(x, ConsSchema)
				errors = v.errors
				return flag, errors,'consumer'
			else:
				flag = False
				errors = 'Unable to validate'
				return flag, errors, 'ERROR - INVALID INPUT'
		except:
			print('Something went wrong')
			raise
