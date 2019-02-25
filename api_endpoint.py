#!flask/bin/python
from flask import Flask
from flask import request
from flask import jsonify
import pandas as pd
import numpy as np
import pickle
import json
import os
import boto3
import subprocess
from flask import send_file, after_this_request

class InvalidInput(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


app = Flask(__name__)

@app.route('/isAlive')
def index():
    return "true mf"

@app.route('/start_server', methods=['GET','POST'])
def start_server():
    #content = request.get_json(silent=True)
    username = 'rondo'
    directory = '/Users/varadarajanganesan/Git/test-terraform/' + username + '/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    private_key_path  = directory + username + ".pem"
    if not os.path.isfile(private_key_path) or os.path.getsize(private_key_path) == 0:   
        ec2 = boto3.client("ec2")
        ec2.delete_key_pair(KeyName = username)  
        keypair = ec2.create_key_pair(KeyName = username)
        filehandler = open(private_key_path, "w")
        filehandler.write(keypair['KeyMaterial'])
        filehandler.close()
        subprocess.run(["chmod","400",private_key_path])

    session = boto3.Session()
    aws_credentials = session.get_credentials()

    private_key_path_json_path = "${file(\"" + private_key_path + "\")}"   
    terraform_json = {}
    terraform_json["resource"] = {}
    terraform_json["resource"]["aws_instance"] = {}
    terraform_json["resource"]["aws_instance"]["configuration"] = {"ami" : "ami-01e24be29428c15b2", "instance_type": "t2.micro", "key_name": username}
    terraform_json["resource"]["aws_instance"]["configuration"]["connection"] = {"private_key": private_key_path_json_path, "type": "ssh", "user" : "ec2-user", "timeout" : "1m"}
    terraform_json["resource"]["aws_instance"]["configuration"]["provisioner"] = {}
    terraform_json["resource"]["aws_instance"]["configuration"]["provisioner"]["remote-exec"] = {"script": directory + "script.sh"}
    terraform_json["provider"] = {}
    # Provider needs to changed based on user's input in the future.
    terraform_json["provider"]["aws"] = {"access_key": aws_credentials.access_key , "secret_key": aws_credentials.secret_key, "region": "us-west-2"} 

    with open(directory + 'configuration.tf', 'w') as f:
        json.dump(terraform_json, f)

    @after_this_request
    def remove_file(response):
        try:
            os.remove(private_key_path)
        except Exception as error:
            print("Error removing or closing downloaded file handle")
        return response
    return send_file(private_key_path, as_attachment = True, attachment_filename = username + ".pem")


@app.errorhandler(InvalidInput)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

if __name__ == '__main__':
    app.run(port=5000,host='0.0.0.0')        
    # app.run(debug=True)