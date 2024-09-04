from dataclasses import dataclass
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "file_records.db")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION: str = os.getenv("AWS_DEFAULT_REGION")
    SQS_QUEUE_NAME: str = os.getenv("SQS_QUEUE_NAME")
    SQS_QUEUE_URL: str = os.getenv("SQS_QUEUE_URL")
    GMAIL_CREDS_FILE_PATH: str = os.getenv("GMAIL_CREDS_FILE_PATH", "smtp/creds/credentials.json")
    GMAIL_TOKEN_FILE_PATH: str = os.getenv("GMAIL_TOKEN_FILE_PATH", "smtp/creds/token.json")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME")
    S3_FOLDER_PATH: str = os.getenv("S3_FOLDER_PATH", "files/")
    LOCAL_DOWNLOAD_FOLDER_PATH: str = os.getenv("LOCAL_DOWNLOAD_FOLDER_PATH", "smtp/files/")
    UPLOAD_TO_S3: bool = os.getenv("UPLOAD_TO_S3", "True") == "True"
    FLASK_APP_HOST: str = os.getenv("FLASK_APP_HOST", "127.0.0.1")
    FLASK_APP_PORT: int = int(os.getenv("FLASK_APP_PORT", "5000"))
    TRANSFORM_API_ENDPOINT: str = f"http://{FLASK_APP_HOST}:{FLASK_APP_PORT}/endpoint"
    

    # SFTP configuration
    # SFTP_HOST: str = "localhost"
    # SFTP_PORT: int = 22
    # SFTP_USER: str = "sftpuser"
    # SFTP_PASSWORD: str = "12345"
    # SFTP_UPLOAD_PATH: str = "/uploads"