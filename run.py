import os
from flask import Flask, request, redirect, url_for, abort, render_template, send_from_directory
from werkzeug.utils import secure_filename
import yaml
import sys

#import shutil
from app.Methods.yaml2json import convert2json
from app.Methods.yamlchecker import yamlValidator, fileValidator
from app.Methods.requestController import messageForwarder


base_dir = os.path.dirname(os.path.dirname(__file__))
UPLOAD_FOLDER_DESC = os.path.join(os.sep, base_dir,'uploads')

if not os.path.exists(UPLOAD_FOLDER_DESC):
    os.makedirs(UPLOAD_FOLDER_DESC)
ALLOWED_EXTENSIONS = {'yaml', 'yml', 'json'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER_DESC'] = UPLOAD_FOLDER_DESC
app.secret_key = 'meson'

def isAllowedFile(f):
	'''
	Checks whether an uploaded file is in the correct format (extension-based)
	'''
	return '.' in f and f.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['POST', 'GET'])
def home():
	'''
	Loads the MESON Agent webpage
	Handles valid and invalid nstD and appD uploads 
	'''

	if request.method == 'GET':
		return render_template('home.html')

	if request.method == 'POST':
		# if the post request has not the file part, redirect the user to the 'upload form' page 			
		if not request.files.get('file', None):
			return redirect(request.url)
		uploaded_files = request.files.getlist("file")
		if len(uploaded_files) != 2:
			message = 'You should upload exactly two files (nstD and appD).'
			return error(message)
		for my_file in uploaded_files:
			filename = secure_filename(my_file.filename).lower()
			if isAllowedFile(filename):
				# store the filename in a secure version
				my_file.save(os.path.join(app.config['UPLOAD_FOLDER_DESC'], filename))
				# if the file is not a text file
				if not fileValidator(filename, UPLOAD_FOLDER_DESC):
					os.remove(os.path.join(os.sep, app.config['UPLOAD_FOLDER_DESC'], filename))
					message = 'Invalid input. Input file has an accepted extension, but not accepted content.'
					return error(message)
				#check if the file is an AppD or a nst 
				if 'nst' in filename:
					# TODO: check for nst correctness 
					##with open(os.path.join(os.sep, UPLOAD_FOLDER_DESC ,filename), 'r') as yaml_in:
					##	nstD = yaml.safe_load(yaml_in)
					nstD =(os.path.join(app.config['UPLOAD_FOLDER_DESC'], filename))
					#print(nstD) 
				elif 'appd' in filename:
					flag, errors, role = yamlValidator(filename, UPLOAD_FOLDER_DESC)
					if flag:
						appD = convert2json(filename, UPLOAD_FOLDER_DESC)
					else:
						os.remove(os.path.join(app.config['UPLOAD_FOLDER_DESC'], filename))
						message = 'Invalid appD. Schema validation failed with error: \n {}.'.format(errors)
						return error(message)
				# if appd or nst is not in the filename
				else:
					os.remove(os.path.join(app.config['UPLOAD_FOLDER_DESC'], filename))
					message = 'Invalid filename \'{0}\'. Filenames should include either \'appD\' or \'nst\'.'.format(filename)
					return error(message)
			else:
				return error('Invalid input. Input file is either empty or does not have an accepted extension.')
		message = messageForwarder(appD, nstD, role)
#		shutil.rmtree(UPLOAD_FOLDER_DESC, ignore_errors=False) 
		if 'Error' in message:

			return error(message)	
		else:
			return success(message)		


@app.route('/error/<message>')
def error(message):
	return render_template('error.html', msg=message)

@app.route('/success/<message>')
def success(message):
	return render_template('success.html', msg=message)

if __name__ == "__main__":
	app.run(debug=True, port=8000)
