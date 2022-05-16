# -*- coding: utf-8 -*-
"""
Created on Tue May  4 15:24:04 2021

@author: ATPL1049
"""

import sys
import glob
import pprint
import json
from sqlalchemy import create_engine
import os
import boto3
import datetime
import requests
import pandas
import time as tm

from CrashMetrics import *
from V2_Impact_Util_Functions import ReadImpactJson
# import matplotlib
# from matplotlib import pyplot as plt

# https://dev.to/razcodes/how-to-create-a-lambda-using-python-with-dependencies-4846

# cd env/lib/python3.7/site-packages
# zip -r9 ${OLDPWD}/function.zip .
# cd $OLDPWD
# zip -g function.zip lambda_function.py

s3_client = boto3.client("s3") #Intializing "s3" as client
S3_BUCKET = 'samcligit'

def lambda_handler(event,context):   # ~~~~~Object Key = Input Context || object_key = Event

    object_key= event['queryStringParameters']['object_key']
    #. Load the Impact JSON in form of JSON using "json.loads"
#    object_key = "18000c52-b501-4eef-ae62-3903d08a46c2_crashVisDict.json"  # replace object key
    file_content = s3_client.get_object(                                   # To get the "file/object" from "s3"
               Bucket=S3_BUCKET, Key=object_key)["Body"].read()

#3. Load the Impact JSON in form of JSON using "json.loads"    
    crashvis_dict = json.loads(file_content);
#    crashvis_dict = event['queryStringParameters']['crashvis_dict']
    
#------def lambda_handler(crashvis_json_string)
#------crashvis_dict = json.loads(crashvis_json_string);    

    crashmetrics_json_string = CrashMetrics(crashvis_dict)
        
    crashmetrics_json_string = json.dumps(crashmetrics_json_string)

    return {
            'statusCode': 200,
            "body": crashmetrics_json_string
            }
