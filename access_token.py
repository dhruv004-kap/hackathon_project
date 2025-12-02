import os
import requests
import traceback
import uuid
import base64
import binascii

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def customFunction(phone):

    # === Function to convert ISTtime to UTC === #
    def get_ind_time(utc_time):
        # Parse the string (it already contains timezone info)
        utc_time = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo("UTC"))

        # Convert to IST
        ist_time = utc_time.astimezone(ZoneInfo("Asia/Kolkata"))

        # Convert to str
        str_ist = ist_time.strftime("%Y-%m-%d %H:%M:%S")
        
        return str_ist

    # === Function to generate uuid === #
    def get_uuid():
        return uuid.uuid4().int

    # === Function to generate AES random key === #
    def generate_aes_key_hex():
        # 16 random bytes -> 32 hex chars
        hex_key = binascii.hexlify(os.urandom(16)).decode('utf-8')
        return hex_key

    # === Function to Encrypt secret key === #
    def aes_encrypt_ecb_pkcs5_base64(plain_text: str, aes_key_hex: str) -> str:
        key_bytes = aes_key_hex.encode('utf-8')  # 32 bytes ASCII chars

        # PKCS5/PKCS7 padding
        padded = pad(plain_text.encode('utf-8'), AES.block_size)

        cipher = AES.new(key_bytes, AES.MODE_ECB)
        ct = cipher.encrypt(padded)

        return base64.b64encode(ct).decode('utf-8')

    # === Function to Encrypt AES key === #
    def rsa_encrypt_aes_key_base64(aes_key_hex: str) -> str:
        public_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkGJZ9gZuStr8ZJyDOsZvFN90nqKa+j7GJ4c/eSEY+F4JnQ0A+lzZ75+5xpF1Tey0jCnAbhK6/KJ/xZjwXMMBfOfCCjicmpn5hrkYwEwaM6pCteJc4YigbcQn6PD1Yk5d1hIKDG+2X5P47gGYg8ppJ78svgaOt3hth454Nkhq9EE7rslh8blYiK75ntOX/ikDyYCqM/+7K4jVGVukDcMEPgGCb1Q3nMgXfCfE0e0dSCmY4s/1DkyUxa5AKgRn+u4atM3Zw0lUaG+/W/SF6fTuE6d7lFg+V0GiNNVvqmRQ7t3r8Q8FN1EhLEMai6kUL+3EH6NcqZnwqKtuptJVKkO0bQIDAQAB"

        # decode base64 DER → RSA key
        key_der = base64.b64decode(public_key)
        rsa_key = RSA.import_key(key_der)

        cipher = PKCS1_v1_5.new(rsa_key)
        ciphertext = cipher.encrypt(aes_key_hex.encode("utf-8"))

        return base64.b64encode(ciphertext).decode("utf-8")


    # === config === #
    secret_code = "c3dbe72abc517d25bd05df3d27326863bfaba0974b8e6efd86be526bd90aa4a6"
    client_id = "3063e95e1ac2981fafc2898f68e22332"
    channel_id = "3177"

    phone = "7938564120"
    email = "dummy@gmail.com"

    # generate uuid
    uu_id = get_uuid()
    print(f"\nGenerated UUID: {uu_id}")

    # generate AES key
    hex_key = generate_aes_key_hex()
    print(f"\nGenerated hex key: {hex_key}")

    # Encrypt secret key
    encrypted_secret = aes_encrypt_ecb_pkcs5_base64(secret_code, hex_key)
    print(f"\nEncrypted secret code: {encrypted_secret}")

    # Encrypt AES key
    encrypted_AES = rsa_encrypt_aes_key_base64(hex_key)
    print("\nEncrypted AES Key:", encrypted_AES)


    url = "https://sit-apig.test.jiobank.in/jpb/v1/app/authenticate"
    headers = {
        "x-trace-id": str(uu_id),
        "x-channel-id": channel_id
    }
    params = {
        "x-trace-id": uu_id,
        "x-channel-id": channel_id
    }

    payload = {
        "application": {
            "clientId": client_id,
            "mobile": {
                "mobileNumber": phone,
                "countryCode": "91"
            },
            "emailAddress": email
        },
        "authenticateList": [
            {
                "mode": 20,
                "value": encrypted_secret
            }
        ],
        "scope": "SESSION",
        "purpose": 1,
        "extraInfo": "2000000000120",
        "secure": {
            "encryptionKey": encrypted_AES
        }
    }

    try:
        print(f"\nUrl: {url}, \n\nPayload: {payload}")
        print(f"\nRequest sent at {get_ind_time(datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))}")

        res = requests.post(url=url, headers=headers, params=params, json=payload)

        print(f"\nResponse recieved at {get_ind_time(datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))}")

        st_code = res.status_code
        print(f"\nResponse status code: {st_code}")

        if res.status_code == 200:
            result = res.json()
            print(f"\nResponse: {result}")

            session = result.get("session", {})

            pre_call_res = {
                "access_token": session["accessToken"].get("tokenValue") if session.get("accessToken") else "",
                "trace_id": str(uu_id),
                "app_id": session.get("appIdentifierToken")
            }

            return pre_call_res
        else:
            print(f"Response text: {res.text}")

            return {
                "access_token": "",
                "trace_id": "",
                "app_id": ""
            }

    except Exception as e:
        print(f"\nError during API call: {e}\nTraceback: {traceback.format_exc()}")
        return {"message": "Error occurred during API call for auth token"}


if __name__ == "__main__":
    result = customFunction("9346798520")
    print(f"\nPre_call response: {result}")
