import boto3
from boto3.exceptions import Boto3Error
from io import BytesIO
import pandas as pd
import requests
import json
from transform.utils import df_to_json
from db import DatabaseManager
from config import Config
from utils import new_logger, get_current_time_utc
import os

# Configure logging
logger = new_logger(__name__)

# SQLite3 database setup
dbm = DatabaseManager()


def update_status_as_in_progress(record_dict):
    id = record_dict["id"]
    status = "IN-PROGRESS"
    updated_at = get_current_time_utc()
    # Pass only the necessary parameters for the "IN-PROGRESS" status
    dbm.update_status(id, status, updated_at)

def update_status_as_success(record_dict):
    id = record_dict["id"]
    status = "SUCCESS"    
    updated_at = get_current_time_utc()
    created_at = record_dict["created_at"]
    # Pass both updated_at and created_at for the "SUCCESS" status
    dbm.update_status(id, status, updated_at, created_at)


def update_status_as_error(record_dict):
    id = record_dict["id"]
    created_at = record_dict["created_at"]
    status = "ERROR"
    updated_at = get_current_time_utc()
    dbm.update_status(id, status, updated_at,created_at)

def get_file_from_s3_as_df(file_name):
    aws_access_key_id = Config.AWS_ACCESS_KEY_ID
    aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY
    bucket_name = Config.S3_BUCKET_NAME
    folder = Config.S3_FOLDER_PATH
    s3_key = folder + file_name

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        if response:
            file_extension = os.path.splitext(file_name)[1]
            if file_extension == '.csv':
                df = pd.read_csv(BytesIO(response["Body"].read()))
            else:
                df = pd.read_excel(BytesIO(response["Body"].read()))
            return df
    except Exception as e:
        logger.error(f"Error fetching file from S3: {str(e)}")
    return None

def log_api_request(url, method, payload):
    personalinfo_payload = payload['personalinfo']
    logger.info(f"API Request - Timestamp: {get_current_time_utc()}, URL: {url}, Method: {method}, Payload: {json.dumps(personalinfo_payload)}")

def log_api_response():
    logger.info(f"API Response - Timestamp: {get_current_time_utc()}, Data Received")

def send_api_request(url, json_payload):
    try:
        headers = {'Content-Type': 'application/json'}
        json_payload_data = json.dumps([json_payload], indent=2)
        response = requests.post(url, headers=headers, data=json_payload_data)
        log_api_response()
        return response
    except Exception as e:
        logger.error(f"Error occurred in send_api_request: {str(e)}")
        return None

def process_record(record_dict):
    try:
        api_url = Config.TRANSFORM_API_ENDPOINT
        file_name = record_dict.get("file_name")
        df = get_file_from_s3_as_df(file_name)
        if df is None:
            return False
        json_data_list = df_to_json(df)
        if not json_data_list:
            return False
        for json_data in json_data_list:
            log_api_request(api_url, "POST", json_data)
            response = send_api_request(api_url, json_data)
            if response is None or response.status_code != 200:
                logger.warning("Failed to send API request or received non-200 response")
                return False
        return True
    except Exception as e:
        logger.error(str(e))
        return False

def main():
    record_dict = dbm.get_first_started_record()
    if record_dict:
        try:
            update_status_as_in_progress(record_dict)
            if process_record(record_dict):
                update_status_as_success(record_dict)
            else:
                update_status_as_error(record_dict)
        except Exception as e:
            logger.error(str(e))
            update_status_as_error(record_dict)
    else:
        logger.info("No records to process.")

if __name__ == "__main__":
    main()
