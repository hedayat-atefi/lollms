"""
project: lollms_webui
file: lollms_xtts.py 
author: ParisNeo
description: 
    This module contains a set of FastAPI routes that concerns petals service

"""
from fastapi import APIRouter, Request
from lollms_webui import LOLLMSWebUI
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from lollms.types import MSG_TYPE
from lollms.main_config import BaseConfig
from lollms.utilities import detect_antiprompt, remove_text_from_string, trace_exception, find_first_available_file_index, add_period, PackageManager
from pathlib import Path
from ascii_colors import ASCIIColors
import os
import platform

# ----------------------- Defining router and main class ------------------------------

router = APIRouter()
lollmsElfServer:LOLLMSWebUI = LOLLMSWebUI.get_instance()


# ----------------------- voice ------------------------------

@router.get("/install_vllm")
def install_vllm():
    try:
        lollmsElfServer.ShowBlockingMessage("Installing vllm server\nPlease stand by")
        from lollms.services.vllm.lollms_vllm import install_vllm
        if install_vllm(lollmsElfServer):
            lollmsElfServer.HideBlockingMessage()
            return {"status":True}
        else:
            return {"status":False, 'error':str(ex)}            
    except Exception as ex:
        trace_exception(ex)
        lollmsElfServer.HideBlockingMessage()
        return {"status":False, 'error':str(ex)}
    
@router.get("/start_vllm")
def start_vllm():
    try:
        if not hasattr(lollmsElfServer,"vllm") or lollmsElfServer.vllm is none:
            lollmsElfServer.ShowBlockingMessage("Loading vllm server\nPlease stand by")
            from lollms.services.vllm.lollms_vllm import get_vllm
            if get_vllm(lollmsElfServer):
                lollmsElfServer.HideBlockingMessage()
                return {"status":True}
            else:
                return {"status":False, 'error':str(ex)}            
        else:
            return {"status":False, 'error':'Service already running'}            

    except Exception as ex:
        trace_exception(ex)
        lollmsElfServer.HideBlockingMessage()
        return {"status":False, 'error':str(ex)}
