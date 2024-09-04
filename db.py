import sqlite3
from config import Config
from utils import new_logger
from datetime import datetime
import hashlib


# Configure logging
logger = new_logger(__name__)

class DatabaseManager:
    def __init__(self):
        self.DB_NAME = Config.DATABASE_NAME
        self.create_table()
        self.in_progress_timestamps = {}


    def create_table(self):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS records (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                file_name TEXT NOT NULL,
                                status TEXT NOT NULL,
                                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                email TEXT NOT NULL,
                                duration_seconds REAL
                            )""")
            
            conn.commit()

    def insert_to_db(self, file_data):
        with sqlite3.connect(self.DB_NAME) as conn:
            try:
                cursor = conn.cursor()
                file_name = file_data.get("file_name")
                status = file_data.get("status")
                created_at = file_data.get("created_at")
                updated_at = file_data.get("updated_at")
                email = file_data.get("email")
                duration_seconds = None
                cursor.execute(
                    """INSERT INTO records (file_name, status, created_at, updated_at,email,duration_seconds)
                            VALUES (?, ?, ?, ?, ?,?)""",
                    (file_name, status, created_at, updated_at,email,duration_seconds),
                )
                conn.commit()
            except Exception as e:
                logger.error(str(e))


    def update_status(self, id, status, updated_at, created_at=None):
      with sqlite3.connect(self.DB_NAME) as conn:
        cursor = conn.cursor()
        try:
            if status == "IN-PROGRESS":
                # Store the timestamp for IN-PROGRESS status
                self.in_progress_timestamps[id] = updated_at
                cursor.execute("""UPDATE records SET status = ?, updated_at = ? WHERE id = ?""",
                               (status, updated_at, id))
            elif status == "SUCCESS":
                if id in self.in_progress_timestamps:
                    in_progress_at = self.in_progress_timestamps.pop(id)
                    duration_seconds = (datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S') -
                                        datetime.strptime(in_progress_at, '%Y-%m-%d %H:%M:%S')).total_seconds()
                    duration_seconds = round(duration_seconds, 1)
                    cursor.execute("""UPDATE records SET status = ?, updated_at = ?, duration_seconds = ? WHERE id = ?""",
                                   (status, updated_at, duration_seconds, id))
                else:
                    cursor.execute("""UPDATE records SET status = ?, updated_at = ? WHERE id = ?""",
                                   (status, updated_at, id))
            else:
                cursor.execute("""UPDATE records SET status = ?, updated_at = ? WHERE id = ?""",
                               (status, updated_at, id))
            conn.commit()
        except Exception as e:
            logger.error(str(e))


    def get_first_started_record(self):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    f"""SELECT * FROM records WHERE status = 'STARTED' ORDER BY id ASC LIMIT 1"""
                )
                row = cursor.fetchone()
                if row:
                    file_data = {
                        "id": row[0],
                        "file_name": row[1],
                        "status": row[2],
                        "created_at": row[3],
                        "updated_at": row[4],
                        "email":row[5],
                        "duration_seconds":row[6]
                    }
                    return file_data
            except Exception as e:
                logger.error(str(e))
                
    def get_all_records(self):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """SELECT * FROM records"""
                )
                rows = cursor.fetchall()
                records = []
                for row in rows:
                    file_data = {
                        "id": row[0],
                        "file_name": row[1],
                        "status": row[2],
                        "created_at": row[3],
                        "updated_at": row[4],
                        "email" : row[5],
                        "duration_seconds" : row[6]
                    }
                    records.append(file_data)
                return records
            except Exception as e:
                logger.error(str(e))

    def record_exists(self, file_data):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            try:
                query = """SELECT COUNT(*) FROM records WHERE file_name = ? AND created_at = ?"""
                cursor.execute(query, (file_data['file_name'], file_data['created_at']))
                count = cursor.fetchone()[0]
                return count > 0
            except Exception as e:
                logger.error(f"Error checking if record exists: {str(e)}")
                return False
                

class SmtpDatabaseManager:
    
    def __init__(self):
        self.DB_NAME = Config.DATABASE_NAME
        self.create_table()
    
    def create_table(self):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS smtp_last_run_record (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                status TEXT NOT NULL,
                                last_run_time INTEGER NOT NULL,
                                total_files_downloaded INTEGER NOT NULL
                            )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS smtp_file_status (
                              unique_id TEXT NOT NULL,
                              status TEXT NOT NULL,
                              PRIMARY KEY (unique_id)
                            )""")
            conn.commit()
            
    def insert_to_db(self, status, last_run_time, total_files_downloaded):
        with sqlite3.connect(self.DB_NAME) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO smtp_last_run_record (status, last_run_time, total_files_downloaded)
                            VALUES (?, ?, ?)""",
                    (status, last_run_time, total_files_downloaded),
                )
                conn.commit()
            except Exception as e:
                logger.error(str(e))
                
                
    def get_last_success_run_timestamp(self):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    f"""SELECT last_run_time FROM smtp_last_run_record WHERE status = 'SUCCESS' ORDER BY id DESC LIMIT 1"""
                )
                row = cursor.fetchone()
                if row:
                    return row[0]
            except Exception as e:
                logger.error(str(e))


    def truncate_epoch_time(self , epoch_time):
        dt = datetime.fromtimestamp(epoch_time)
    
        dt_truncated = dt.replace(second=0, microsecond=0)
        epoch_time_truncated = int(dt_truncated.timestamp())
    
        return epoch_time_truncated            

       
    def generate_unique_id(self, message_id, attachment_filename):
        """Generate a unique identifier for each attachment using a hash."""
        unique_string = f"{message_id}-{attachment_filename}"
        return hashlib.sha256(unique_string.encode()).hexdigest()

    def is_attachment_processed(self,unique_id):
        """Check if the attachment has been processed."""
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT status FROM smtp_file_status
                   WHERE unique_id = ?""",
                (unique_id,)
            )
            row = cursor.fetchone()
            if row:
                status = row[0]
                if status in ('processed', 'in_progress'):
                    return True
            return False

    def mark_attachment_as_in_progress(self,unique_id):
        """Mark an attachment as being processed in the database."""
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO smtp_file_status (unique_id, status)
                VALUES (?, ?)""",
                (unique_id, 'in_progress')
            )
            conn.commit()

    def mark_attachment_as_processed(self, unique_id):
        """Mark an attachment as processed in the database."""
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE smtp_file_status SET status = ? 
                WHERE unique_id = ?""",
                ('processed',unique_id)
            )
            conn.commit()

    def mark_attachment_as_failed(self,unique_id):
        """Mark an attachment as failed in the database."""
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE smtp_file_status SET status = ? 
                WHERE unique_id = ?""",
                ('failed',unique_id)
            )
            conn.commit()





                                



                                