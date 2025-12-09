initial_pre_call_template = """import requests
import traceback
from datetime import datetime

def customFunction(phone_number):

"""

current_date_template = """
    # === Getting current date === #
    curr_date = datetime.now().strftime("%d-%m-%Y")
    print(f"\\nCurrent date: {curr_date}")

"""

external_api_call_template = """
    # === make API call to client API === #
    api_url = "api-base-url"    # keep api base url here instead of 'api-url'; 
    # Example: "https://exmaple.com/process?phone=9346852170" then,
    # base URl: https://exmaple.com/process    (add this to api_url)
    # params: phone    (add this params in 'url_params' dictionary)

    api_headers = {
        "Content-Type": "application/json",
        "Authorization": "api-auth-token",    # add auth token instead of 'api-auth-token' if auth token is required else remove this line from code
        "Cookie" : "api-cookies"    # add cookie string instead of 'api-cookies' if cookies are required else remove this line from code
    }

    # add parameter of url in url_params dictionary if requires else remove this 'url_params' dictionary from code
    url_params = {
        "phone": phone_number    # this phone number will be dynamic for each request so added to function parameter in function defination
    }

    # add payload of request body as 'api_payload' dictionary if requires else remove this 'api_payload' dictionary from code
    api_payload = {
        "phone": phone_number    # this phone number will be dynamic for each request so added to function parameter in function defination
    }

    try:
        # if request method is POST then replace request.get with request.post
        api_response = requests.get(
            url=api_url, 
            headers=api_headers,    # Remove this line if headers are not required
            params=url_params,     # Remove this line if params are not required
            json=api_payload    # Remove this line if payload are not required
        )

        api_response.raise_for_status

        api_result = api_response.json()
        print(f"\\nAPI response: {api_result}")

    except Exception as e:
        print(f"\\nError: {e}; \\nTraceback: {traceback.format_exc()}")
        return {
            "error": "Error occured during client API call!"    
        }
    
"""

create_ticket_template = """
    # === create ticket API call === #
    ticket_url = f"create-ticket-url-base-url"
    # Exampls URl: https://clientName.int.kapturecrm.com/kapture-call.html/vitosivb/vitosivb?support_call=support&phone=9346852170&campaign=08047354381&call_type=Inbound&call_id=&emp_code=vitosvb
    # base URl: https://clientName.int.kapturecrm.com/kapture-call.html/vitosivb/vitosivb    (add this to ticket_url)
    # params: support_call, phone, campaign, call_type, call_id, emp_code    (add this params in 'ticket_url_params' dictionary)
    
    ticket_headers = {
        "Content-Type": "application/json",
        "Authorization": "api-auth-token",    # add auth token instead of 'api-auth-token' if auth token is required else remove this line from code
        "Cookie" : "api-cookies"    # add cookie string instead of 'api-cookies' if cookies are required else remove this line from code
    }

    # replace the params (support_call, campaign, call_type, emp_code) values as per the cURL 
    ticket_url_params = {
        "support_call": "support", 
        "phone": phone_number, 
        "campaign": "08047354381", 
        "call_type": "Inbound", 
        "call_id": "", 
        "emp_code": "vitosvb"
    } 

    try:
        ticket_response = requests.post(url=ticket_url, headers=ticket_headers, params=ticket_url_params)
        
        ticket_response.raise_for_status

        res_json = ticket_response.json()
        print(f"\\nCreate ticket response: {res_json}")

    except Exception as e:
        print(f"\\nError: {e}; Traceback: {traceback.format_exc()}")
        return {
            "error": f"Error occured during ticket creation!"
        }

"""

initial_post_call_template = """import json
import requests
import traceback
from typing import Literal
from openai import OpenAI
from pymongo import MongoClient
from pydantic import BaseModel, Field
from datetime import datetime

def customFunction(ticket_id, conversation_id):

    # === Configs === #
    API_KEY = "openai-api-key"    # add OPENAI API key here
    mongo_uri = "db-connection-link"    # add mongodb connection link here
    
    # === MongoDB Connection ===
    client = MongoClient(mongo_uri)
    db = client["vb_platform"]
    be_tp = db["be_tp"] 
    conversation_memory = db["conversation_memory"]

    # getting recording and times from DB
    be_tp_obj = be_tp.find_one({"conversation_id": conversation_id})

    recording_url = be_tp_obj.get("recording_url")
    client_id = be_tp_obj.get("client_id")
    bot_id = be_tp_obj.get("config_id")
    to_phone = be_tp_obj.get("to_phone")
    from_phone = be_tp_obj.get("from_phone")
    start_time = be_tp_obj.get("start_time")
    end_time = be_tp_obj.get("end_time")

    # === Calculating call duration === #
    try:
        print("\\nstart_time: ", start_time, ", end_time: ", end_time)

        format_string = "%Y-%m-%d %H:%M:%S"
       
        if start_time and end_time:
            start_time_obj = datetime.strptime(start_time, format_string)
            end_time_obj = datetime.strptime(end_time, format_string)

            duration = (end_time_obj - start_time_obj).total_seconds()
            print("\\nDuration: ", duration)
        
        else:
            duration = 1
            print("\\nMissing start_time or end_time")

    except Exception as e:
        duration = 1
        print("\\nSome error occured during calculating duration")

    # === Taking conversation from DB === #
    conversation_memory_obj = conversation_memory.find_one({"conversation_id": conversation_id})
    conversation = conversation_memory_obj.get("conversation_history", "")

    formatted_conversation = ""
    for entry in conversation:
        role = entry['role'].capitalize()
        content = entry['content']
        formatted_conversation += f"{role}: {content}\\n"

    # === Response model for openai llm invoke === #
    class response_model(BaseModel):
        # define what details we need to extract from conversaion 
        # format => variable_name: data_type = Field(description="description about the data") 
        # replace below variable and theire description according to requirement and make changes in the prompt accordingly
        customer_name: str = Field(description="name of the customer")
        product_name: str = Field(description="name of the product customer have")
        model_name: str = Field(description="name of the product customer have")
        issue: str = Field(description="issue happening with product")
        address: str  = Field(description="customer full address with landmark")
        pincode: str = Field(description="pincode number (must be 6 digits only)")
        area: str = Field(description="area name")
        city: str  = Field(description="city name")
        connect_to_agent: Literal["Yes", "No"] = Field(description="'Yes' if customer want to talk to human agent else 'No'")

    # === prompt for openai llm invoke === #
    prompt = f\"""You are a professional content extractor.
    Your task is to extract important information from the given conversation in structured manner.(extract all the information in english language only).
    Extract the Following information from the given conversation:
        - customer name,
        - product name,
        - model name,
        - issue,
        - address,
        - pincode,
        - area,
        - city,
        - connect to agent

        Conversation: {formatted_conversation}
    \""" 
    
    # === openai llm invoke === #
    openai_client = OpenAI(api_key=API_KEY)
    try:
        response = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a structured information extractor."},
            {"role": "user", "content": prompt}
        ],
        response_format=response_model,
        temperature=0.2)
        openai_output_response = response.choices[0].message.content
        openai_output = json.loads(openai_output_response)
        print("\\nOpenAi response:\\n", openai_output)

    except json.JSONDecodeError:
        raise ValueError("Failed to parse GPT output")
    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {str(e)}")
    
    # parse openai output
    associate_obj = {
        "customer_name": openai_output.get("customer_name"),
        "product_name": openai_output.get("product_name"),
        "model_name": openai_output.get("model_name"),
        "issue": openai_output.get("issue"),
        "address": openai_output.get("address"),
        "area": openai_output.get("area"),
        "pincode": openai_output.get("pincode"),
        "city": openai_output.get("city"),
        "connect_to_agent": openai_output.get("connect_to_agent")
    }

"""

upload_recording_url_template = """
    # === Uploading Recording URL === #
    try:
        callback_url = "https://clientName.int.kapturecrm.com/ms/ai-service/voice-bot/callback"    # Replace 'clientName' in this url according to the client
        emp_code = "emp-code"    # Replace 'emp-code' 

        recording_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'auth-token'          # add auth token instead of 'api-auth-token' if auth token is required else remove this line from code
        }

        callback_payload = json.dumps({
            "ticketId": ticket_id,
            "ucid": f"@@{client_id}@@{bot_id}@@{conversation_id}@@",
            "recording": recording_url,
            "duration": str(duration),
            "agentId": emp_code,
            "dialStatus": "completed",
            "from": from_phone,    # if call direction is inbound then replace 'from_phone' with 'to_phone'
            "to": to_phone,        # if call direction is inbound then replace 'to_phone' with 'from_phone'
            "callType": "inbound/outbound",    # change the call direction according to usecase
        })

        print("\\nPOSTING RECORDING URL")
        response = requests.post(url=callback_url, headers=recording_headers, data=callback_payload)

        if response.status_code == 200 :
            print("\\nUploading voice recording url: Success")
            print(f"\\nUploading Recording URL response: {response}")
        else :
            print("\\nUploading voice recording url: Failed")
            print(f"\\nUploading Recording URL response: {response}")

    except Exception as e:
        print(f"\\nError occured during uploading recording url! \\nTraceback: {traceback.format_exc()}")
    
"""

update_dashboard_template = """
    # === Dashboard updation === #
    dashboard_url = "https://clientName.int.kapturecrm.com/ms/ticket-order/voice-bot/noauth/update-call-details"    # Replace 'clientName' in this url according to the client
    dashboard_headers = {
        "Content-Type":"application/json"    # add Authorization if required
    }

    dashboard_payload = {
        "uploader_id": None,
        "client_id": client_id,
        "config_id": be_tp_obj.get("config_id"),   
        "coversation_id": conversation_id,
        "ticket_id": ticket_id,
        "call_sid": be_tp_obj.get("call_sid"),
        "call_queue_id": be_tp_obj.get("call_queue_id"),
        "call_queue_object_id": "",
        "call_duration": str(duration),
        "call_direction": "Inbound/Outbound",    # change the call direction according to usecase
        "call_recording": recording_url,
        "call_attempt": 1,
        "call_timestamp": start_time,
        "telephony_status": "completed",
        "associate_object": [associate_obj],
        "cx_metrics": {},
        "use_case": "",    # add the use case name if have any
        "call_extras": {
            "call_started": start_time,
            "call_ended": end_time
        },
        "tag_id": None
    }
    print(f"\\nDashboard payload: {dashboard_payload}")

    try:
        dashboard_response = requests.post(url=dashboard_url, headers=dashboard_headers, json=dashboard_payload)
        res_status_code = dashboard_response.status_code

        if res_status_code == 200:
            dashboard_res = dashboard_response.text
            print(f"\\nStatus code: {res_status_code}, \\nDashboard Response: {dashboard_res}")

        else:
            dashboard_res = dashboard_response.text
            print(f"\\nStatus code: {res_status_code}, \\nDashboard Response: {dashboard_res}")

    except Exception as e:
        print(f"\\nSome error occured during updating dashboard webhook; Error: {e}; \\nTraceback: {traceback.format_exc()}")
            
"""

ticket_updation_template = """
    # === Update ticket === #
    ticket_url = "https://clientame.int.kapturecrm.com/update-ticket-from-other-source.html/v.2.0"    # Replace 'clientName' in this url according to the client

    ticket_headers = {
        "Content-Type" : "application/json",
        "Authorization": "api-auth-token",    # add auth token instead of 'api-auth-token' if auth token is required else remove this line from code
        "Cookie" : "api-cookies"              # add cookie string instead of 'api-cookies' if cookies are required else remove this line from code
    }

    ticket_payload = [{
        "comment": "",
        "ticket_id": ticket_id,
        "callback_time": "",
        "sub_status": "RS",
        "queue": "",
        "disposition": "",
        "associate_objects": associate_obj    # Replace the 'associate_objects' with the param name as per the payload in cURL
    }]

    try:
        response = requests.post(url=ticket_url, headers=ticket_headers, json=ticket_payload)
        res_status = response.status_code
        print(f"\\nTicket updation response status: {res_status}")

        if res_status == 200:
            res_json = response.json()
            print(f"\\nCreate ticket response: {res_json}")

            return {
                "ticket_id": ticket_id,
                "ticket_updated": res_status == 200,
                "associate_obj": associate_obj
            }
        
        else:
            res_text = response.text
            print(f"\\nResponse text: {res_text}")

            return {
                "error": "ticket updation failed!",
                "ticket_updated": res_status == 200
            }
        
    except Exception as e:
        print(f"\\nError: {e}; \\nTraceback: {traceback.format_exc}")
        return {
            "error": f"error occured during ticket updation!"
        }
"""


current_date_time_template = """from datetime import datetime
from zoneinfo import ZoneInfo

def customFunction():

    # Get current date time in Indian timezone
    ist_time = datetime.now().astimezone(ZoneInfo("Asia/Kolkata"))

    # Convert to str
    str_ist = ist_time.strftime("%Y-%m-%d %H:%M:%S")
    
    return str_ist
"""


convert_digit_to_words_template = """def convert_number_to_word(number):
    digits = {
        "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
        "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
    }

    num = ""

    for n in number:
        num += digits.get(n) + " "

    return {
        "number_in_words": num[:-1]
    }
"""