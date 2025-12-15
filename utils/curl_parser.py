import shlex
import json
from typing import Dict, Optional, Any

def parse_url(url: str) -> tuple[str, dict[str, str]]:
    """Parse the url and return base url & params"""
    if "?" in url:
        url, params_str = url.split("?", 1)
        params = {}

        if params_str:
            for param in params_str.split("&"):
                if "=" in param:
                    key, val = param.split("=", 1)
                    params[key.strip()] = val.strip()
        
        return url, params
    
    return url, {}

def build_recursive_payload(data: Any, dynamic_map: Dict[str, str], current_path: str = "") -> str:
    """
    Recursively builds a Python dictionary string representation.
    It replaces values with variable names if the key or path exists in dynamic_map.
    """
    
    # 1. Handle Dictionaries (Nested Objects)
    if isinstance(data, dict):
        items = []
        for key, value in data.items():
            # Create the path for dot-notation
            new_path = f"{current_path}.{key}" if current_path else key

            if new_path in dynamic_map:
                var_name = dynamic_map[new_path]
                items.append(f"'{key}': {var_name}")
            
            elif key in dynamic_map:
                var_name = dynamic_map[key]
                items.append(f"'{key}': {var_name}")
            
            else:
                value_str = build_recursive_payload(value, dynamic_map, new_path)
                items.append(f"'{key}': {value_str}")
        
        # Join items to look like a python dict string
        return "{" + ", ".join(items) + "}"

    # Handle Lists
    elif isinstance(data, list):
        items = [build_recursive_payload(item, dynamic_map, current_path) for item in data]
        return "[" + ", ".join(items) + "]"

    # Handle Primitives (Strings, Ints, Booleans, None)
    else:
        # automatically adds quotes for strings and handles numbers/bools correctly
        return repr(data)

def generate_simple_dict(dict_name: str, data: dict, dynamic_keys: dict) -> str:
    """Helper to make dictionaries as flat sting like Headers and Params"""

    if not data:
        return f"    {dict_name} = {{}}"

    lines = [f"    {dict_name} = {{"]
    for key, value in data.items():
        if key in dynamic_keys:
            lines.append(f"        '{key}': {dynamic_keys[key]},")
    
        else:
            # Escape quotes
            safe_val = str(value).replace('"', '\\"').replace("'", "\\'")
            lines.append(f"        '{key}': '{safe_val}',")
    
    lines.append("    }")

    return "\n".join(lines)


def parse_curl(curl_command: str, dynamic_map: Optional[Dict[str, Dict[str, str]]] = None) -> str:
    """
    Generate python code for api from provided cURL

    Args:
        curl_command (str): entire curl as string format 

    Returns:
        str: python code for given api curl

    dynamic_map structure example:
    {
        "headers": {
            "token": "auth_token"                    # Simple key match
        }
        "json": {
            "ticketID": "ticket_id"                  # Simple key match
            "user.address.city": "city_var",         # Dot notation for nested
        }
    }
    """

    if dynamic_map is None:
        dynamic_map = {"params": {}, "headers": {}, "json": {}}

    # === Parse cURL === #
    try:
        tokens = shlex.split(curl_command)
    except Exception as e:
        raise ValueError(f"Failed to parse cURL: {e}")

    if tokens[0] != "curl":
        raise ValueError("Input must start with curl")

    method = "GET"
    url = None
    headers = {}
    params = {}
    data_str = None

    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token in ("-X", "--request"):
            method = tokens[i + 1].upper()
            i += 2
        elif token in ("-H", "--header"):
            header = tokens[i + 1]
            if ":" in header:
                key, value = header.split(":", 1)
                headers[key.strip()] = value.strip()
            i += 2
        elif token in ("-d", "--data", "--data-raw", "--data-urlencode", "--data-binary"):
            data_str = tokens[i + 1]
            i += 2
        elif token.startswith("http"):
            if "?" in token:
                url, url_params = parse_url(token)
                params.update(url_params)
            else:
                url = token
            i += 1
        else:
            i += 1

    if not url:
        raise ValueError("No URL found")

    # === Process Payload === #
    payload_data = None
    if data_str:
        try:
            payload_data = json.loads(data_str)
            if method == "GET": method = "POST"
        except:
            payload_data = {"raw_data": data_str}

    # === Build Function Signature === #
    args_list = []
    all_dynamic_vars = set()
    
    # Gather all unique variable names for the function definition
    for category in ["params", "headers", "json"]:
        if category in dynamic_map:
            for _, var_name in dynamic_map[category].items():
                if var_name not in all_dynamic_vars:
                    args_list.append(f"{var_name}: str")
                    all_dynamic_vars.add(var_name)
    
    args_str = ", ".join(args_list)

    # === Generate Code === #
    code = [
        "import requests",
        "import json",
        "import traceback",
        "",
        f"def customFunction({args_str}):",
        f'    url = "{url}"',
    ]

    # Headers & Params (Flat structures)
    code.append(generate_simple_dict("headers", headers, dynamic_map.get("headers", {})))
    code.append(generate_simple_dict("params", params, dynamic_map.get("params", {})))

    # Payload (Nested structure)
    if payload_data:
        if "raw_data" in payload_data and len(payload_data) == 1:
            code.append(f"    payload = '{payload_data['raw_data']}'")
        else:
            # Use the recursive builder here
            json_map = dynamic_map.get("json", {})
            # This generates a string that looks like a python dict but with unquoted variables
            dict_code_str = build_recursive_payload(payload_data, json_map)
            

            code.append(f"    payload_dict = {dict_code_str}")
            code.append("    payload = json.dumps(payload_dict)")
    else:
        code.append("    payload = None")

    # API Request Execution
    api_hit_code = [
            "",
            "    try:",
            f"        response = requests.request('{method}', url, headers=headers, params=params, data=payload)",
            "        res_status = response.status_code",
            "        print(f\"\\nResponse status code: {res_status}\")",
            "",
            "        if res_status == 200:",
            "            res_json = response.json()",
            "            print(f\"\\nResponse: {res_json}\")",
            "            return res_json",
            "",
            "        else:",
            "            res_text = response.text",
            "            print(f\"Response text: {res_text}\")",
            "            return {\"message\": f\"request failed with status code: {res_status}\", \"error\": res_text}",
            "",
            "    except Exception as e:",
            "        print(f\"\\nError: {e}; \\nTraceback: {traceback.format_exc()}\")",
            "        return {\"message\": \"Error occured!\"}"
        ]

    code.extend(api_hit_code)

    return "\n".join(code)



if __name__ == "__main__":
    # Raw cURL
    curl_cmd = """curl 'https://api.example.com/users?page=1&limit=10' \
    -H 'Authorization: Bearer static_key' \
    -H 'Content-Type: application/json' \
    -d '{
        "order_id": "123",
        "customer": {
            "name": "John",
            "address": {
                "city": "Paris",
                "zip": "75000"
            }
        }
    }'"""

    # dynamic values config
    dynamic_config = {
        "headers": {
            "Authorization": "auth_token"
        },
        "params": {
            "page": "page_no"
        },
        "json": {
            "order_id": "order_id",        
            "customer.name": "customer_name",      
            "customer.address.city": "city_name",
            "customer.address.zip": "pincode" 
        }
    }

    # Generate Code
    generated_python = parse_curl(curl_cmd, dynamic_config)
    print(generated_python)



