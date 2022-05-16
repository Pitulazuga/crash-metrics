# -*- coding: utf-8 -*-
"""
Created on Tue May  4 15:24:04 2021

@author: ATPL1049
"""

import json
from sqlalchemy import create_engine
import os
import boto3

import datetime


from CrashDetect_PyFiles import CallCD_V21
from V2_Impact_Util_Functions import ReadImpactJson
# import matplotlib
# from matplotlib import pyplot as plt

# https://dev.to/razcodes/how-to-create-a-lambda-using-python-with-dependencies-4846

# cd env/lib/python3.7/site-packages
# zip -r9 ${OLDPWD}/function.zip .
# cd $OLDPWD
# zip -g function.zip lambda_function.py
#

def lambda_handler(event, context):
    """
    Main lambda function that takes in query parameters and returns the desired computation.
    """
    # parse query parameters
    query_parameters = event["params"]["querystring"]
    filename = query_parameters.get("filename", "NONE")
    DataVisualizationFlag = query_parameters.get('DataVisualization', False)
    debug_flag = query_parameters.get('DEBUG', False)

    # parse request body data
    event_context = event["context"]
    request_body = event["body-json"]

    # process request body data
    #TODO Update this function using the last deployed version of Crash ID!!!
    impactData = ReadImpactJson(request_body["records"], filename, debug_flag); # Only get the data for more plotting and exploration.

    # run parameters
    DEBUG = {}
    # This is what I use to run it locally with debugging and evaluation.
    # DEBUG can be left empty (i.e. {}) in production.
    DEBUG['PLT'] = False
    DEBUG['EVAL'] = False
    DEBUG['numProcessed'] = 0

    Parameters = {}
    Parameters['DataVisualization'] = DataVisualizationFlag
    Parameters['DEBUG'] = DEBUG
    Parameters['Filename'] = filename

    # process the crash!
    impact_response = CallCD_V21(impactData,Parameters)

    # save any relevant images
    session = boto3.Session()
    s3 = session.resource("s3")
    bucket_name = os.getenv("image_output_bucket")

    position = filename.index('.json')
    cleaned_filename = filename[0:position]

    if impact_response["IS_CRASH"]:
        os.chdir('/tmp')

        crash_viz_one_fn = f"{cleaned_filename}_CrashVis_AccelXY_SpeedOBD.pdf"
        crash_viz_one_qualified_fn = f"/tmp/{crash_viz_one_fn}"
        crash_viz_two_fn = f"{cleaned_filename}_CrashVis_GPSlonLat_SpeedOBD.pdf"
        crash_viz_two_qualified_fn = f"/tmp/{crash_viz_two_fn}"

        result = s3.Bucket(bucket_name).upload_file(crash_viz_one_qualified_fn,f"CrashViz/{crash_viz_one_fn}")
        result = s3.Bucket(bucket_name).upload_file(crash_viz_two_qualified_fn,f"CrashViz/{crash_viz_two_fn}")


    if DataVisualizationFlag:
        # WRITE FILES TO S3
        os.chdir('/tmp')
        impact_viz_one_fn = f"{cleaned_filename}_ImpactVis_AccelXY_SpeedOBD.pdf"
        impact_viz_one_qualified_fn = f"/tmp/{impact_viz_one_fn}"

        impact_viz_two_fn = f"{cleaned_filename}_ImpactVis_GPSlonLat_SpeedOBD.pdf"
        impact_viz_two_qualified_fn = f"/tmp/{impact_viz_two_fn}"

        result = s3.Bucket(bucket_name).upload_file(impact_viz_one_qualified_fn,f"ImpactViz/{impact_viz_one_fn}")
        result = s3.Bucket(bucket_name).upload_file(impact_viz_two_qualified_fn,f"ImpactViz/{impact_viz_two_fn}")


    # conn_str =  generate_connection_string()
    # engine = create_engine(conn_str)
    # log_call(event_context["api-key"], event_context["resource-path"])

    return {
        'statusCode': 200,
        "body": impact_response
    }


def log_call(token, call_type):
    """
    Basic API logging.
    """

    conn_str = generate_connection_string(database = "crud")
    engine = create_engine(conn_str)

    tm = datetime.datetime.now().isoformat()

    QUERY = f"INSERT INTO token_usage(token, tm, endpoint) VALUES ('{token}', '{tm}', '{call_type}');"
    with engine.connect() as connection:
        result = connection.execute(QUERY)


def generate_connection_string(database = None):
    """
    Pull environment variables and construct a mysql connection string.
    """

    host = os.getenv("host")
    user = os.getenv("user")
    password = os.getenv("password")
    database = database or os.getenv("database")

    return f"mysql+pymysql://{user}:{password}@{host}/{database}"

