import boto3
from config import Config
from db import DatabaseManager
from utils import new_logger, format_iso_date
import os

os.environ["AWS_ACCESS_KEY_ID"] = Config.AWS_ACCESS_KEY_ID
os.environ["AWS_SECRET_ACCESS_KEY"] = Config.AWS_SECRET_ACCESS_KEY
os.environ["AWS_DEFAULT_REGION"] = Config.AWS_DEFAULT_REGION

logger = new_logger(__name__)

s3_client = boto3.client('s3')

class S3FileProcessor:
    def __init__(self):
        self.db = DatabaseManager()
    
    def get_unprocessed_files(self):
        paginator = s3_client.get_paginator('list_object_versions')
        file_info = []

        for page in paginator.paginate(Bucket=Config.S3_BUCKET_NAME, Prefix='files/'):
            versions = page.get('Versions', [])
            for version in versions:
                file_key = version['Key']
                version_id = version['VersionId']
                if file_key.endswith('/'):
                    continue
                
                obj = s3_client.head_object(Bucket=Config.S3_BUCKET_NAME, Key=file_key, VersionId=version_id)
                last_modified = obj['LastModified']
                file_info.append((file_key, version_id, last_modified))
        
        processed_files = self.db.get_all_records()
        processed_file_info = [(record['file_name'], record['created_at']) for record in processed_files]
        
        unprocessed_files = [(file_key, last_modified) for file_key, _, last_modified in file_info 
                              if (self.extract_file_name(file_key), format_iso_date(last_modified.isoformat())) not in processed_file_info]
        
        return unprocessed_files
    
    def extract_file_name(self, file_key):
        parts = file_key.split('/')
        if len(parts) > 1:
            return parts[-1]
        else:
            logger.warning(f"Invalid file_key format: {file_key}")
            return ''

    def process_files(self):
        unprocessed_files = self.get_unprocessed_files()
        
        if not unprocessed_files:
            logger.info("No new files to process.")
            return
        
        for file_key, last_modified in unprocessed_files:
            try:
                # Fetch metadata from S3 object
                obj = s3_client.head_object(Bucket=Config.S3_BUCKET_NAME, Key=file_key)
                metadata = obj.get('Metadata', {})
                
                # Check if required metadata fields are present
                email = metadata.get('email')
                if not email:
                    logger.warning(f"Missing metadata for file_key: {file_key}. Skipping file.")
                    continue
                
                # Extract file name from the key
                file_name = self.extract_file_name(file_key)
                
                # Check the file name and metadata
                logger.info(f"Processing file_name: {file_name}, last_modified: {last_modified}")
                
                if not file_name:
                    logger.warning(f"Empty file name detected for file_key: {file_key}")
                    continue
                
                # Define file data
                file_data = {
                    "file_name": file_name,
                    "status": "STARTED",
                    "created_at": format_iso_date(last_modified.isoformat()),
                    "updated_at": format_iso_date(last_modified.isoformat()),  
                    "email": email
                }
                
                # Check if record already exists
                if not self.db.record_exists(file_data):
                    # Insert file data into the database
                    self.db.insert_to_db(file_data)
                    logger.info(f"File inserted into DB")
                else:
                    logger.info(f"File already exists in DB, skipping insertion.")
            
            except Exception as e:
                logger.error(f"Error processing file : {str(e)}")

if __name__ == "__main__":
    processor = S3FileProcessor()
    processor.process_files()
