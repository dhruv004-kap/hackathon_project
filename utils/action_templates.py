from utils.action_template_components import *

# === function to get pre_call template === #
def get_pre_call_template(external_api: bool = False, current_date: bool = False):

    pre_call_template = initial_pre_call_template

    # append external api call code
    if external_api:
        pre_call_template += external_api_call_template

    # append current date code 
    if current_date:
        pre_call_template += current_date_template

    # append create ticket code
    pre_call_template += create_ticket_template

    # append result returning code
    pre_call_template += """    # The variable name give here are accessible in prompt via prompt input variable (in prompt variable name should be same as given here)
    result = {
        "ticket_id": res_json.get("ticket_id"),
        "phone": phone_number,
"""
    
    # append external api response to pre_call result
    if external_api:
        pre_call_template += """        "user_name": api_result.get("userName"),    # accessing user name from client API response (replace userName with the required data)
        # add more data here if required from client API response in similar way to user_name
"""
    
    # append current date to pre_call result
    if current_date:
        pre_call_template += """        "current_date": curr_date,
"""

    pre_call_template += """    }
    
    return result"""

    return {
        "code_template": pre_call_template,
        "params": [{
            "param_name": "phone_number",
            "data_type": "str",
            "param_description": "customer phone number"
        }]
    }


# === function to get post_call template === #
def get_post_call_template(external_api: bool = False, update_dashboard: bool = False, upload_recording: bool = False):
    post_call_template = initial_post_call_template
    
    # append external api call code
    if external_api:
        post_call_template += external_api_call_template

    # append update dashboard code
    if update_dashboard:
        post_call_template += update_dashboard_template

    # append upload recording code
    if upload_recording:
        post_call_template += upload_recording_url_template

    # append update ticket code
    post_call_template += ticket_updation_template

    return {
        "code_template": post_call_template,
        "params": [{
            "param_name": "ticket_id",
            "data_type": "str",
            "param_description": "ticket id"
        },
        {
            "param_name": "conversation_id",
            "data_type": "str",
            "param_description": "conversation id"
        }
        ]
    }

# === function to get tool for get current date and time === #
def get_tool_current_date_time():
    return {
        "code_template": current_date_time_template,
        "params": None
    }

# === function to get tool for convert digit to words === #
def get_tool_digits_to_words():
    return {
        "code_template": convert_digit_to_words_template,
        "params": [{
            "param_name": "number",
            "data_type": "str",
            "param_description": "number to convert in words"
        }]
    }