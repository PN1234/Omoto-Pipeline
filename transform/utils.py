from utils import new_logger

# Configure logging
logger = new_logger(__name__)

def df_to_json(df):
    try:
        json_data = []

        for _, row in df.iterrows():
            personalinfo = {
                "firstname": row["FIRSTNAME"],
                "lastname": row["LASTNAME"],
                "email": row["EMAIL"],
                "mobileno": str(row["PHONE"]),
                "regid": str(row["REGISTRATIONID"]),
                "unitname": "Shriram life"
            }

            qualifyinginfo = [
                {"name": "final_channel", "value": row["FINAL_CHANNEL"]},
                {"name": "agtloc_state", "value": row["AGTLOC_STATE"]},
                {"name": "age", "value": str(row["AGE"])},
                {"name": "selectedLanguageForSurvey", "value": ""},
                {"name": "occupation", "value": row["OCCUPATION"]},
                {"name": "receipt_date", "value": row["RECEIPT_DATE"]},
                {"name": "plan_type", "value": row["PLAN_TYPE"]},
                {"name": "paying_term", "value": str(row["PAYING_TERM"])},
                {"name": "policy_number", "value": str(row["POLICY_NUMBER"])},
                {"name": "touch_point", "value": str(row["TOUCH_POINT"])},
                {"name": "policy_term", "value": str(row["POLICY_TERM"])},
                {"name": "plan_name", "value": row["PLAN_NAME"]},
                {"name": "state", "value": row["CUSTOMER_STATE"]},
                {"name": "gender", "value": row["GENDER"]},
                {"name": "date_of_commencement", "value": row["DATE_OF_COMMENCEMENT"]},
                {"name": "education", "value": row["EDUCATION"]},
                {"name": "city", "value": row["CITY"]},
                {"name": "mode", "value": row["MODE"]},
                {"name": "receipt_no", "value": str(row["RECEIPT_NO"])}
            ]

            record = {
                "personalinfo": personalinfo,
                "qualifyinginfo": qualifyinginfo
            }

            json_data.append(record)

        return json_data

    except Exception as e:
        logger.error(f"Error occurred in excel_to_json: {str(e)}")
        return None
    
    
# def send_api_request(url, json_payload):
#     try:
#         headers = {'Content-Type': 'application/json'}        
#         response = requests.post(url, headers=headers, json=json_payload)   
#         return response     
#     except Exception as e:
#         logger.error(f"Error occurred in send_api_request: {str(e)}")
#         return None
