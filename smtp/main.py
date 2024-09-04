import time
from smtp.gmail_manager import GmailManager
from config import Config
from db import SmtpDatabaseManager
from utils import new_logger

# Configure logging
logger = new_logger(__name__)

def main():
    dbm = SmtpDatabaseManager()
    last_run_timestamp = dbm.get_last_success_run_timestamp()
    if last_run_timestamp is None:
        last_run_timestamp = int(time.time()) - 60 * 60

    buffer_time = 10 * 60
    adjusted_timestamp = last_run_timestamp - buffer_time 
    query = f"after:{adjusted_timestamp} is:unread"
    
    #query = f"after:{last_run_timestamp} is:unread"

    subject_line = "Sample Excel File"
    #senders = ["neemapriyal1405@gmail.com"]
    required_columns = {
        "REGISTRATIONID", "FIRSTNAME", "LASTNAME", "EMAIL", "PHONE", "UNITNAME", 
        "TRANSACTIONID", "POLICY_NUMBER", "RECEIPT_NO", "RECEIPT_DATE", "TOUCH_POINT", 
        "AGTLOC_STATE", "FINAL_CHANNEL", "CITY", "CUSTOMER_STATE", "PLAN_NAME", 
        "PLAN_TYPE", "DATE_OF_COMMENCEMENT", "MODE", "POLICY_TERM", "PAYING_TERM", 
        "AGE", "GENDER", "OCCUPATION", "EDUCATION"
    }
    try:
        gmail = GmailManager()
        msgs = gmail.fetch_emails_with_query(query)

        filtered_msgs = gmail.filter_messages(messages=msgs, subject=subject_line)
        

        if Config.UPLOAD_TO_S3:
            s3_bucket_name = Config.S3_BUCKET_NAME
            s3_folder_path = Config.S3_FOLDER_PATH
            access_key = Config.AWS_ACCESS_KEY_ID
            secret_key = Config.AWS_SECRET_ACCESS_KEY
            gmail.upload_attachments_to_s3(messages=filtered_msgs, bucket_name=s3_bucket_name, folder_path=s3_folder_path, access_key=access_key, secret_key=secret_key,required_columns=required_columns)            
        else:
            local_folder_path = Config.LOCAL_DOWNLOAD_FOLDER_PATH
            gmail.download_attachments_local(messages=filtered_msgs, local_folder_path=local_folder_path)
            logger.info(f"Downloaded {len(filtered_msgs)} files from emails to {local_folder_path}")
        current_time = int(time.time())    
        last_run_timestamp = dbm.truncate_epoch_time(current_time)
        dbm.insert_to_db(status="SUCCESS", last_run_time=last_run_timestamp, total_files_downloaded=len(msgs))
        logger.info('Updated last successful run timestamp')
    except Exception as e:
        logger.error(f"Error occurred while running the function: {str(e)}")
        dbm.insert_to_db(status="ERROR", last_run_time=int(time.time()), total_files_downloaded=len(msgs))

if __name__ == '__main__':
    main()



