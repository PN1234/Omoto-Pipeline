import os
import base64
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import boto3
import hashlib
from config import Config
from utils import new_logger
import pandas as pd
from datetime import datetime , timezone
from db import SmtpDatabaseManager
# Configure logging
logger = new_logger(__name__)

class GmailManager:
    def __init__(self, creds_filepath=Config.GMAIL_CREDS_FILE_PATH, token_filepath=Config.GMAIL_TOKEN_FILE_PATH):
        self.SCOPES=['https://www.googleapis.com/auth/gmail.readonly']
        self.creds_filepath = creds_filepath
        self.token_filepath = token_filepath
        self.creds = self.authenticate_gmail()
        self.service = build('gmail', 'v1', credentials=self.creds)
        
    def authenticate_gmail(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists(self.token_filepath):
            creds = Credentials.from_authorized_user_file(self.token_filepath, self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds_filepath, self.SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open(self.token_filepath, 'w') as token:
                token.write(creds.to_json())
        return creds
    
    
    def fetch_emails_with_query(self, query):
        results = self.service.users().messages().list(userId='me', labelIds=['INBOX'], q=query).execute()
        messages = results.get('messages', [])
        return messages
    
    def _get_attachment_data(self, gmail_message, part):
        if 'data' in part['body']:
            return part['body']['data']
        else:
            attachment_id = part['body']['attachmentId']
            attachment = self.service.users().messages().attachments().get(
                userId='me', messageId=gmail_message['id'], id=attachment_id).execute()
            return attachment['data']

    def download_attachments_local(self, messages, local_folder_path):
        os.makedirs(local_folder_path, exist_ok=True)

        for message in messages:
            gmail_message = self.service.users().messages().get(userId='me', id=message['id']).execute()

            for part in gmail_message['payload']['parts']:
                if 'filename' in part:
                    attachment_data = self._get_attachment_data(gmail_message, part)
                    file_path = os.path.join(local_folder_path, part['filename'])
                    with open(file_path, 'wb') as file:
                        file.write(base64.urlsafe_b64decode(attachment_data.encode('UTF-8')))


    def generate_unique_id(self, message, part):
        message_id = message['id']
        filename = part.get('filename', 'unknown')
        mime_type = part.get('mimeType', 'unknown')
        unique_string = f"{message_id}_{filename}_{mime_type}"
        return hashlib.md5(unique_string.encode('utf-8')).hexdigest()
    


    def verify_columns(self, file_stream, file_extension, required_columns):
        """Check if the file (in-memory) contains the required columns based on its extension."""
        try:
            if file_extension in {'.xlsx', '.xls'}:
                df = pd.read_excel(file_stream)
            elif file_extension == '.csv':
                df = pd.read_csv(file_stream)
            else:
                logger.error(f"Unsupported file extension: {file_extension}")
                return False
            
            columns = df.columns.tolist()
            #print(columns)
            
            return all(column in columns for column in required_columns)
        except Exception as e:
            logger.error(f"Error verifying columns: {e}")
            return False
                        
    def upload_attachments_to_s3(self, messages, bucket_name, folder_path, access_key, secret_key,required_columns):
        """Upload attachments from a list of Gmail messages to an S3 bucket."""
        dbm = SmtpDatabaseManager()
        
        s3 = boto3.client('s3', aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key)

        
        allowed_extensions = {'.csv', '.xlsx', '.xls'}
        
        uploaded_files_count = 0
        
        for message in messages:
            gmail_message = self.service.users().messages().get(userId='me', id=message['id']).execute()
            #print(gmail_message)
            headers = gmail_message['payload']['headers']
            email_address = None
            for header in headers:
                if header['name'].lower() == 'from':
                    email_address = header['value']
                    email_address = email_address.split(" ")[-1]
                    email_address = email_address.strip('<>')
                    break
            if not email_address:
                continue
            for part in gmail_message['payload']['parts']:
                if part.get('filename'):
                    file_extension = os.path.splitext(part['filename'])[1].lower()
                    if file_extension in allowed_extensions:
                        attachment_data = self._get_attachment_data(gmail_message, part)
                        file_data = base64.urlsafe_b64decode(attachment_data.encode('UTF-8'))
                        unique_id = self.generate_unique_id(message, part)
                        if dbm.is_attachment_processed(unique_id):
                            logger.info(f"Skipped file (currently being processed or already processed): {part['filename']}")
                            continue

                        dbm.mark_attachment_as_in_progress(unique_id)
                        
                        file_stream = io.BytesIO(file_data)
               
                        #print(file_stream)
                        if not self.verify_columns(file_stream, file_extension, required_columns):
                            logger.info(f"Skipped file due to missing columns: {part['filename']}")
                            dbm.mark_attachment_as_failed(unique_id)
                            continue
                        file_stream.seek(0)
                        s3_key = os.path.join(folder_path, part['filename'])
                        try:
                            last_modified_timestamp = datetime.now(tz=timezone.utc).isoformat()
                            s3.put_object(Body=file_data, Bucket=bucket_name, Key=s3_key,Metadata={'email': email_address,'last_modified':last_modified_timestamp})
                            uploaded_files_count += 1
                            logger.info(f"Uploaded file: {part['filename']}")
                            dbm.mark_attachment_as_processed(unique_id)
                        except Exception as e:
                            logger.error(f"Failed to upload attachment {part['filename']}: {str(e)}")
                            dbm.mark_attachment_as_failed(unique_id)
 
                    else:
                        logger.info(f"Skipped file with unsupported extension: {part['filename']}")
        logger.info(f"Uploaded {uploaded_files_count} files from emails")   
        

    def filter_messages(self, messages, subject):
        filtered_messages = []
        for message in messages:
            gmail_message = self.service.users().messages().get(userId='me', id=message['id']).execute()
            headers = gmail_message['payload']['headers']
            
            # Extract the subject header
            subject_header = next((header['value'] for header in headers if header['name'].lower() == 'subject'), None)
            
            # Check if the subject header contains the specified subject
            if subject_header and subject in subject_header:
                filtered_messages.append(message)

        return filtered_messages



    # def filter_messages(self, messages, subject, senders):
    #     filtered_messages = []
    #     for message in messages:
    #         gmail_message = self.service.users().messages().get(userId='me', id=message['id']).execute()
    #         headers = gmail_message['payload']['headers']
    #         email_address = None
    #         for header in headers:
    #             if header['name'].lower() == 'from':
    #                 email_address = header['value']
    #                 email_address = email_address.split(" ")[-1]
    #                 email_address = email_address.strip('<>')
    #                 break
    #         if not email_address:
    #             continue

    #     # Check if the email address matches any of the specified senders
    #         if email_address in senders:
    #             subject_header = next((header['value'] for header in headers if header['name'].lower() == 'subject'), None)
    #             if subject_header and subject in subject_header:
    #                 filtered_messages.append(message)
    #     return filtered_messages



