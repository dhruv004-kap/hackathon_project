import os
import re
import traceback

from fastapi import APIRouter, Depends, HTTPException, status

from pymongo import MongoClient

from models import *
from Routers.auth import verify_basic_auth
from action_template import *


DB_URI = os.getenv("DB_URI")

conn = MongoClient(DB_URI)
db = conn["vb_platform"]
prompt_library = db["prompt_library"]


library = APIRouter(
    prefix="/prompt-library",
    tags=["Prompt_library"]
)


@library.get("/prompt-components")
async def get_prompt_components(auth: str = Depends(verify_basic_auth)):
    """ This is end poin to get available prompts components """
    try:
        return list(prompt_library.find({"component_type": "prompt_component"}, {"_id": 0}))
    
    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error!")


@library.get("/get-service-types")
async def get_service_types(auth: str = Depends(verify_basic_auth)):
    """ This is end poin to get available industry for prompts """

    try:
        # get available industries from DB
        service_types_record = prompt_library.find({"component_type": "prompt"}, {"service_type": 1, "_id": 0})

        service_types = []

        for doc in service_types_record:
            service_types.append(doc.get("service_type"))

        return set(service_types)
    
    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error!")


@library.get("/get-prompt-languages")
async def get_prompt_languages(auth: str = Depends(verify_basic_auth)):
    """ This is end poin to get available languages for prompts """

    try:
        # get available prompts from DB
        languages_records = prompt_library.find({"component_type": "prompt"}, {"language": 1, "_id": 0})

        languages = []

        for doc in languages_records:
            languages.append(doc.get("language"))

        return set(languages)
    
    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error!")
    

@library.get("/prompts")
async def get_prompts(service_type: str, language: str = None, auth: str = Depends(verify_basic_auth)):
    """ This end point for prompt library """

    try:
        # get prompts from DB for selected industry
        db_query = {"service_type": {"$regex": re.compile(service_type, re.IGNORECASE)}}

        if language:
            db_query.update({"language": re.compile(language, re.IGNORECASE)})

        available_prompt = list(prompt_library.find(db_query, {"_id": 0}))

        return available_prompt
    
    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error!")