from flask import Flask, request, render_template, jsonify
import json
import logging
from db import DatabaseManager
from utils import new_logger

app = Flask(__name__)

# Configure logging
logger = new_logger(__name__)
file_handler = logging.FileHandler('app.log')
logger.addHandler(file_handler)

# SQLite3 database setup
dbm = DatabaseManager()


@app.route('/endpoint', methods=['POST'])
def fake_endpoint():
    try:
        json_payload_str = request.data.decode('utf-8')
        json_payload = json.loads(json_payload_str)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {str(e)}")
        json_payload = None
    
    response_data = {
        "message": "Received data successfully!",
        "data_received": json_payload
    }
    return jsonify(response_data), 200


@app.route('/')
def index():
    try:
        rows = dbm.get_all_records()
    except Exception as e:
        rows = []
        logger.error(f"Error fetching data: {str(e)}")
    return render_template('index.html', data=rows)



if __name__== '__main__':
    app.run(debug=True,host="127.0.0.1", port=9000)