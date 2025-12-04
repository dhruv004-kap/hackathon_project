import os
import json
from uuid import uuid4
import re

from dotenv import load_dotenv

from typing import Optional

from fastapi import FastAPI
from pymongo import MongoClient

from curl_parser import parse_curl

from code_helper import graph, system_message
from langchain_core.messages import SystemMessage, HumanMessage

from models import *

from action_template import *

load_dotenv()

app = FastAPI(title="Prompt Library & Action builder")

DB_URI = os.getenv("DB_URI")

conn = MongoClient(DB_URI)
db = conn["prompt_library"]
prompt_collection = db["prompts"]
prompt_component_collection = db["prompt_components"]


@app.get("/")
async def welcome():
    return {"message": "Hello!"}

@app.get("/prompt_library/prompt-components")
async def get_prompt_components():
    """ This is end poin to get available prompts components """
    return list(prompt_component_collection.find({}, {"_id": 0}))

@app.get("/prompt_library/get-service-types")
async def get_service_types():
    """ This is end poin to get available industry for prompts """

    # get available industries from DB
    service_types_record = prompt_collection.find({}, {"service_type": 1, "_id": 0})

    service_types = []

    for doc in service_types_record:
        service_types.append(doc.get("service_type"))

    return set(service_types)


@app.get("/prompt_library/get-prompt-languages")
async def get_service_types():
    """ This is end poin to get available languages for prompts """

    # get available prompts from DB
    languages_records = prompt_collection.find({}, {"language": 1, "_id": 0})

    languages = []

    for doc in languages_records:
        languages.append(doc.get("language"))

    return set(languages)


@app.get("/prompt_library/prmopts")
async def get_prompts(service_type: str, language: str = None):
    """ This end point for prompt library """

    # get prompts from DB for selected industry
    db_query = {"service_type": {"$regex": re.compile(service_type, re.IGNORECASE)}}

    if language:
        db_query.update({"language": re.compile(language, re.IGNORECASE)})

    available_prompt = list(prompt_collection.find(db_query, {"_id": 0}))

    return available_prompt


@app.get("/action-template")
async def get_action_template(action_name: str):
    """ This end point provides action templates """
    return pre_call_template if action_name == "pre_call" else post_call_template


@app.post("/tools/curl_function")
async def get_functions(user_req: function_request):
    """ This end point serve to create python function from curl """

    curl_str = user_req.curl_command
    dynamic_map = json.loads(user_req.dynamic_map)

    python_code = parse_curl(curl_str, dynamic_map)

    return {
        "python_code": python_code
    }


@app.post("/tools/build_tool")
async def build_function(user_req: tool_request):
    """ This end point serve AI Assist """

    user_prompt = user_req.user_prompt
    uu_id = user_req.uu_id

    if not uu_id:
        uu_id = str(uuid4())
        config = {
            "configurable": {"thread_id": uu_id}
        }

        result = graph.invoke({"messages": [HumanMessage(content=user_prompt)]}, config=config)
        
    else:
        result = graph.invoke({"messages": [SystemMessage(content=system_message), HumanMessage(content=user_prompt)]}, config={"configurable": {"thread_id": uu_id}})

    return {
        "result": result["messages"][-1].content,
        "uu_id": uu_id
    }
