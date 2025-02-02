"""
project: lollms
file: lollms_personalities_infos.py 
author: ParisNeo
description: 
    This module contains a set of FastAPI routes that provide information about the Lord of Large Language and Multimodal Systems (LoLLMs) Web UI
    application. These routes are specific to handling personalities related operations.

"""
from fastapi import APIRouter, Request
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import pkg_resources
from lollms.server.elf_server import LOLLMSElfServer
from lollms.personality import AIPersonality, InstallOption
from ascii_colors import ASCIIColors
from lollms.utilities import load_config, trace_exception, gc
from pathlib import Path
from typing import List, Optional
import psutil
import yaml

# --------------------- Parameter Classes -------------------------------

class PersonalityListingInfos(BaseModel):
    category:str


class PersonalitySelectionInfos(BaseModel):
    id:int

# ----------------------- Defining router and main class ------------------------------
router = APIRouter()
lollmsElfServer = LOLLMSElfServer.get_instance()

# --------------------- Listing -------------------------------

@router.get("/list_personalities_categories")
def list_personalities_categories():
    personalities_categories_dir = lollmsElfServer.lollms_paths.personalities_zoo_path  # replace with the actual path to the models folder
    personalities_categories = ["custom_personalities"]+[f.stem for f in personalities_categories_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
    return personalities_categories

@router.get("/list_personalities")
def list_personalities(category:str):
    if not category:
        return []
    try:
        if category=="custom_personalities":
            personalities_dir = lollmsElfServer.lollms_paths.custom_personalities_path  # replace with the actual path to the models folder
        else:
            personalities_dir = lollmsElfServer.lollms_paths.personalities_zoo_path/f'{category}'  # replace with the actual path to the models folder
        personalities = [f.stem for f in personalities_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
    except Exception as ex:
        personalities=[]
        ASCIIColors.error(f"No personalities found. Using default one {ex}")
    return personalities

@router.get("/get_all_personalities")
def get_all_personalities():
    ASCIIColors.yellow("Listing all personalities")
    personalities_folder = lollmsElfServer.lollms_paths.personalities_zoo_path
    personalities = {}

    for category_folder in  [lollmsElfServer.lollms_paths.custom_personalities_path] + list(personalities_folder.iterdir()):
        cat = category_folder.stem
        if category_folder.is_dir() and not category_folder.stem.startswith('.'):
            personalities[cat if category_folder!=lollmsElfServer.lollms_paths.custom_personalities_path else "custom_personalities"] = []
            for personality_folder in category_folder.iterdir():
                pers = personality_folder.stem
                if personality_folder.is_dir() and not personality_folder.stem.startswith('.'):
                    personality_info = {"folder":personality_folder.stem}
                    config_path = personality_folder / 'config.yaml'
                    if not config_path.exists():
                        """
                        try:
                            shutil.rmtree(str(config_path.parent))
                            ASCIIColors.warning(f"Deleted useless personality: {config_path.parent}")
                        except Exception as ex:
                            ASCIIColors.warning(f"Couldn't delete personality ({ex})")
                        """
                        continue                                    
                    try:
                        scripts_path = personality_folder / 'scripts'
                        personality_info['has_scripts'] = scripts_path.exists()
                        with open(config_path, "r", encoding="utf8") as config_file:
                            config_data = yaml.load(config_file, Loader=yaml.FullLoader)
                            personality_info['name'] = config_data.get('name',"No Name")
                            personality_info['description'] = config_data.get('personality_description',"")
                            personality_info['disclaimer'] = config_data.get('disclaimer',"")
                            
                            personality_info['author'] = config_data.get('author', 'ParisNeo')
                            personality_info['version'] = config_data.get('version', '1.0.0')
                            personality_info['installed'] = (lollmsElfServer.lollms_paths.personal_configuration_path/f"personality_{personality_folder.stem}.yaml").exists() or personality_info['has_scripts']
                            personality_info['help'] = config_data.get('help', '')
                            personality_info['commands'] = config_data.get('commands', '')
                        languages_path = personality_folder/ 'languages'

                        real_assets_path = personality_folder/ 'assets'
                        assets_path = Path("personalities") / cat / pers / 'assets'
                        gif_logo_path = assets_path / 'logo.gif'
                        webp_logo_path = assets_path / 'logo.webp'
                        png_logo_path = assets_path / 'logo.png'
                        jpg_logo_path = assets_path / 'logo.jpg'
                        jpeg_logo_path = assets_path / 'logo.jpeg'
                        svg_logo_path = assets_path / 'logo.svg'
                        bmp_logo_path = assets_path / 'logo.bmp'

                        gif_logo_path_ = real_assets_path / 'logo.gif'
                        webp_logo_path_ = real_assets_path / 'logo.webp'
                        png_logo_path_ = real_assets_path / 'logo.png'
                        jpg_logo_path_ = real_assets_path / 'logo.jpg'
                        jpeg_logo_path_ = real_assets_path / 'logo.jpeg'
                        svg_logo_path_ = real_assets_path / 'logo.svg'
                        bmp_logo_path_ = real_assets_path / 'logo.bmp'

                        if languages_path.exists():
                            personality_info['languages']= [""]+[f.stem for f in languages_path.iterdir() if f.suffix==".yaml"]
                        else:
                            personality_info['languages']=None
                            
                        personality_info['has_logo'] = png_logo_path.is_file() or gif_logo_path.is_file()
                        
                        if gif_logo_path_.exists():
                            personality_info['avatar'] = str(gif_logo_path).replace("\\","/")
                        elif webp_logo_path_.exists():
                            personality_info['avatar'] = str(webp_logo_path).replace("\\","/")
                        elif png_logo_path_.exists():
                            personality_info['avatar'] = str(png_logo_path).replace("\\","/")
                        elif jpg_logo_path_.exists():
                            personality_info['avatar'] = str(jpg_logo_path).replace("\\","/")
                        elif jpeg_logo_path_.exists():
                            personality_info['avatar'] = str(jpeg_logo_path).replace("\\","/")
                        elif svg_logo_path_.exists():
                            personality_info['avatar'] = str(svg_logo_path).replace("\\","/")
                        elif bmp_logo_path_.exists():
                            personality_info['avatar'] = str(bmp_logo_path).replace("\\","/")
                        else:
                            personality_info['avatar'] = ""
                        
                        personalities[cat if category_folder!=lollmsElfServer.lollms_paths.custom_personalities_path else "custom_personalities"].append(personality_info)
                    except Exception as ex:
                        ASCIIColors.warning(f"Couldn't load personality from {personality_folder} [{ex}]")
                        trace_exception(ex)
    ASCIIColors.green("OK")

    return personalities


@router.get("/list_mounted_personalities")
def list_mounted_personalities():
    ASCIIColors.yellow("- Listing mounted personalities")
    return {"status": True,
            "personalities":lollmsElfServer.config["personalities"],
            "active_personality_id":lollmsElfServer.config["active_personality_id"]
            }   




@router.get("/get_current_personality_path_infos")
def get_current_personality_path_infos():
    if lollmsElfServer.personality is None:
        return {
            "personality_category":"", 
            "personality_name":""
        }
    else:
        return {
            "personality_category":lollmsElfServer.personality_category, 
            "personality_name":lollmsElfServer.personality_name
        }

# ----------------------------------- Installation/Uninstallation/Reinstallation ----------------------------------------


class PersonalityIn(BaseModel):
    name: str = Field(None)

@router.post("/reinstall_personality")
async def reinstall_personality(personality_in: PersonalityIn):
    """
    Endpoint to reinstall personality

    :param personality_in: PersonalityIn contans personality name.
    :return: A JSON response with the status of the operation.
    """
    try:
        if(".." in personality_in.name):
            raise "Detected an attempt of path traversal. Are you kidding me?"
        if not personality_in.name:
            personality_in.name=lollmsElfServer.config.personalities[lollmsElfServer.config["active_personality_id"]]
        personality_path = lollmsElfServer.lollms_paths.personalities_zoo_path / personality_in.name
        ASCIIColors.info(f"- Reinstalling personality {personality_in.name}...")
        ASCIIColors.info("Unmounting personality")
        idx = lollmsElfServer.config.personalities.index(personality_in.name)
        print(f"index = {idx}")
        lollmsElfServer.mounted_personalities[idx] = None
        gc.collect()
        try:
            lollmsElfServer.mounted_personalities[idx] = AIPersonality(personality_path,
                                        lollmsElfServer.lollms_paths, 
                                        lollmsElfServer.config,
                                        model=lollmsElfServer.model,
                                        app=lollmsElfServer,
                                        run_scripts=True,installation_option=InstallOption.FORCE_INSTALL)
            return {"status":True}
        except Exception as ex:
            ASCIIColors.error(f"Personality file not found or is corrupted ({personality_in.name}).\nReturned the following exception:{ex}\nPlease verify that the personality you have selected exists or select another personality. Some updates may lead to change in personality name or category, so check the personality selection in settings to be sure.")
            ASCIIColors.info("Trying to force reinstall")
            return {"status":False, 'error':str(e)}

    except Exception as e:
        return {"status":False, 'error':str(e)}


# ------------------------------------------- Files manipulation -----------------------------------------------------

@router.get("/get_current_personality_files_list")
def get_current_personality_files_list():
    if lollmsElfServer.personality is None:
        return {"state":False, "error":"No personality selected"}
    return {"state":True, "files":[{"name":Path(f).name, "size":Path(f).stat().st_size} for f in lollmsElfServer.personality.text_files]+[{"name":Path(f).name, "size":Path(f).stat().st_size} for f in lollmsElfServer.personality.image_files]}

@router.get("/clear_personality_files_list")
def clear_personality_files_list():
    if lollmsElfServer.personality is None:
        return {"state":False, "error":"No personality selected"}
    lollmsElfServer.personality.remove_all_files()
    return {"state":True}
class RemoveFileData(BaseModel):
    name:str
    
@router.post("/remove_file")
def remove_file(data:RemoveFileData):
    """
    Removes a file form the personality files
    """
    if lollmsElfServer.personality is None:
        return {"state":False, "error":"No personality selected"}
    lollmsElfServer.personality.remove_file(data.name)
    return {"state":True}




# ------------------------------------------- Mounting/Unmounting/Remounting ------------------------------------------------
class PersonalityDataRequest(BaseModel):
    category:str
    name:str

@router.post("/get_personality_config")
def get_personality_config(data:PersonalityDataRequest):
    print("- Recovering personality config")
    category = data.category
    name = data.name

    package_path = f"{category}/{name}"
    if category=="custom_personalities":
        package_full_path = lollmsElfServer.lollms_paths.custom_personalities_path/f"{name}"
    else:            
        package_full_path = lollmsElfServer.lollms_paths.personalities_zoo_path/package_path
    
    config_file = package_full_path / "config.yaml"
    if config_file.exists():
        with open(config_file,"r") as f:
            config = yaml.safe_load(f)
        return {"status":True, "config":config}
    else:
        return {"status":False, "error":"Not found"}
    
class PersonalityConfig(BaseModel):
    category:str
    name:str
    config:dict
    
@router.post("/set_personality_config")
def set_personality_config(data:PersonalityConfig):
    print("- Recovering personality config")
    category = data.category
    name = data.name
    config = data.config

    package_path = f"{category}/{name}"
    if category=="custom_personalities":
        package_full_path = lollmsElfServer.lollms_paths.custom_personalities_path/f"{name}"
    else:            
        package_full_path = lollmsElfServer.lollms_paths.personalities_zoo_path/package_path
    
    config_file = package_full_path / "config.yaml"
    if config_file.exists():
        with open(config_file,"w") as f:
            yaml.safe_dump(config, f)
        return {"status":True}
    else:
        return {"status":False, "error":"Not found"}

class PersonalityMountingInfos(BaseModel):
    category:str
    folder:str
    language:Optional[str] = None

@router.post("/mount_personality")
def mount_personality(data:PersonalityMountingInfos):
    print("- Mounting personality")
    category = data.category
    name = data.folder
    language = data.language #.get('language', None)

    package_path = f"{category}/{name}"
    if category=="custom_personalities":
        package_full_path = lollmsElfServer.lollms_paths.custom_personalities_path/f"{name}"
    else:            
        package_full_path = lollmsElfServer.lollms_paths.personalities_zoo_path/package_path
    
    config_file = package_full_path / "config.yaml"
    if config_file.exists():
        if language:
            package_path += ":" + language
        """
        if package_path in lollmsElfServer.config["personalities"]:
            ASCIIColors.error("Can't mount exact same personality twice")
            return jsonify({"status": False,
                            "error":"Can't mount exact same personality twice",
                            "personalities":lollmsElfServer.config["personalities"],
                            "active_personality_id":lollmsElfServer.config["active_personality_id"]
                            })                
        """
        lollmsElfServer.config["personalities"].append(package_path)
        lollmsElfServer.mounted_personalities = lollmsElfServer.rebuild_personalities()
        lollmsElfServer.config["active_personality_id"]= len(lollmsElfServer.config["personalities"])-1
        lollmsElfServer.personality = lollmsElfServer.mounted_personalities[lollmsElfServer.config["active_personality_id"]]
        ASCIIColors.success("ok")
        if lollmsElfServer.config["active_personality_id"]<0:
            ASCIIColors.error("error:active_personality_id<0")
            return {"status": False,
                            "error":"active_personality_id<0",
                            "personalities":lollmsElfServer.config["personalities"],
                            "active_personality_id":lollmsElfServer.config["active_personality_id"]
                            }         
        else:
            if lollmsElfServer.config.auto_save:
                ASCIIColors.info("Saving configuration")
                lollmsElfServer.config.save_config()
            ASCIIColors.success(f"Personality {name} mounted successfully")
            return {"status": True,
                            "personalities":lollmsElfServer.config["personalities"],
                            "active_personality_id":lollmsElfServer.config["active_personality_id"]
                            }    
    else:
        pth = str(config_file).replace('\\','/')
        ASCIIColors.error(f"nok : Personality not found @ {pth}")            
        ASCIIColors.yellow(f"Available personalities: {[p.name for p in lollmsElfServer.mounted_personalities]}")
        return {"status": False, "error":f"Personality not found @ {pth}"}


@router.post("/remount_personality")
def remount_personality(data:PersonalityMountingInfos):
    category = data.category
    name = data.folder
    language = data.language #.get('language', None)


    package_path = f"{category}/{name}"
    if category=="custom_personalities":
        package_full_path = lollmsElfServer.lollms_paths.custom_personalities_path/f"{name}"
    else:            
        package_full_path = lollmsElfServer.lollms_paths.personalities_zoo_path/package_path
    
    config_file = package_full_path / "config.yaml"
    if config_file.exists():
        ASCIIColors.info(f"Unmounting personality {package_path}")
        index = lollmsElfServer.config["personalities"].index(f"{category}/{name}")
        lollmsElfServer.config["personalities"].remove(f"{category}/{name}")
        if lollmsElfServer.config["active_personality_id"]>=index:
            lollmsElfServer.config["active_personality_id"]=0
        if len(lollmsElfServer.config["personalities"])>0:
            lollmsElfServer.mounted_personalities = lollmsElfServer.rebuild_personalities()
            lollmsElfServer.personality = lollmsElfServer.mounted_personalities[lollmsElfServer.config["active_personality_id"]]
        else:
            lollmsElfServer.personalities = ["generic/lollms"]
            lollmsElfServer.mounted_personalities = lollmsElfServer.rebuild_personalities()
            lollmsElfServer.personality = lollmsElfServer.mounted_personalities[lollmsElfServer.config["active_personality_id"]]


        ASCIIColors.info(f"Mounting personality {package_path}")
        lollmsElfServer.config["personalities"].append(package_path)
        lollmsElfServer.config["active_personality_id"]= len(lollmsElfServer.config["personalities"])-1
        lollmsElfServer.mounted_personalities = lollmsElfServer.rebuild_personalities()
        lollmsElfServer.personality = lollmsElfServer.mounted_personalities[lollmsElfServer.config["active_personality_id"]]
        ASCIIColors.success("ok")
        if lollmsElfServer.config["active_personality_id"]<0:
            return {"status": False,
                            "personalities":lollmsElfServer.config["personalities"],
                            "active_personality_id":lollmsElfServer.config["active_personality_id"]
                            }      
        else:
            return {"status": True,
                            "personalities":lollmsElfServer.config["personalities"],
                            "active_personality_id":lollmsElfServer.config["active_personality_id"]
                            }    
    else:
        pth = str(config_file).replace('\\','/')
        ASCIIColors.error(f"nok : Personality not found @ {pth}")
        ASCIIColors.yellow(f"Available personalities: {[p.name for p in lollmsElfServer.mounted_personalities]}")
        return {"status": False, "error":f"Personality not found @ {pth}"}  
    

@router.post("/unmount_personality")
def unmount_personality(data:PersonalityMountingInfos):
    print("- Unmounting personality ...")
    category = data.category
    name = data.folder
    language = data.language #.get('language', None)

    try:
        personality_id = f"{category}/{name}" if language is None or language=="" else f"{category}/{name}:{language}"
        index = lollmsElfServer.config["personalities"].index(personality_id)
        lollmsElfServer.config["personalities"].remove(personality_id)
        if lollmsElfServer.config["active_personality_id"]>=index:
            lollmsElfServer.config["active_personality_id"]=0
        if len(lollmsElfServer.config["personalities"])>0:
            lollmsElfServer.mounted_personalities = lollmsElfServer.rebuild_personalities()
            lollmsElfServer.personality = lollmsElfServer.mounted_personalities[lollmsElfServer.config["active_personality_id"]]
        else:
            lollmsElfServer.personalities = ["generic/lollms"]
            lollmsElfServer.mounted_personalities = lollmsElfServer.rebuild_personalities()
            if lollmsElfServer.config["active_personality_id"]<len(lollmsElfServer.mounted_personalities):
                lollmsElfServer.personality = lollmsElfServer.mounted_personalities[lollmsElfServer.config["active_personality_id"]]
            else:
                lollmsElfServer.config["active_personality_id"] = -1
        ASCIIColors.success("ok")
        if lollmsElfServer.config.auto_save:
            ASCIIColors.info("Saving configuration")
            lollmsElfServer.config.save_config()
        return {
                    "status": True,
                    "personalities":lollmsElfServer.config["personalities"],
                    "active_personality_id":lollmsElfServer.config["active_personality_id"]
                    }
    except Exception as ex:
        trace_exception(ex)
        if language:
            ASCIIColors.error(f"nok : Personality not found @ {category}/{name}:{language}")
        else:
            ASCIIColors.error(f"nok : Personality not found @ {category}/{name}")
            
        ASCIIColors.yellow(f"Available personalities: {[p.name for p in lollmsElfServer.mounted_personalities if p is not None]}")
        return {"status": False, "error":"Couldn't unmount personality"}
    

@router.get("/unmount_all_personalities")
def unmount_all_personalities():
    lollmsElfServer.config.personalities=["generic/lollms"]
    lollmsElfServer.mounted_personalities=[]
    lollmsElfServer.personality=None
    lollmsElfServer.mount_personality(0)
    lollmsElfServer.config.save_config()
    return {"status":True}



# ------------------------------------------- Selecting personality ------------------------------------------------

@router.post("/select_personality")
def select_personality(data:PersonalitySelectionInfos):
    ASCIIColors.info("Selecting personality")
    id = data.id
    print(f"- Selecting active personality {id} ...",end="")
    if id<len(lollmsElfServer.mounted_personalities):
        lollmsElfServer.config["active_personality_id"]=id
        lollmsElfServer.personality:AIPersonality = lollmsElfServer.mounted_personalities[lollmsElfServer.config["active_personality_id"]]
        if lollmsElfServer.personality.processor:
            lollmsElfServer.personality.processor.selected()
        ASCIIColors.success("ok")
        print(f"Selected {lollmsElfServer.personality.name}")
        if lollmsElfServer.config.auto_save:
            ASCIIColors.info("Saving configuration")
            lollmsElfServer.config.save_config()
        return {
            "status": True,
            "personalities":lollmsElfServer.config["personalities"],
            "active_personality_id":lollmsElfServer.config["active_personality_id"]                
            }
    else:
        ASCIIColors.error(f"nok : personality id out of bounds @ {id} >= {len(lollmsElfServer.mounted_personalities)}")
        return {"status": False, "error":"Invalid ID"}
            
# ------------------------------------------- Personality settings------------------------------------------------

@router.post("/get_personality_settings")
def get_personality_settings(data:PersonalityMountingInfos):
    print("- Retreiving personality settings")
    category = data.category
    name = data.folder

    if category == "custom_personalities":
        personality_folder = lollmsElfServer.lollms_paths.personal_personalities_path/f"{name}"
    else:
        personality_folder = lollmsElfServer.lollms_paths.personalities_zoo_path/f"{category}"/f"{name}"

    personality = AIPersonality(personality_folder,
                                lollmsElfServer.lollms_paths, 
                                lollmsElfServer.config,
                                model=lollmsElfServer.model,
                                app=lollmsElfServer,
                                run_scripts=True)
    if personality.processor is not None:
        if hasattr(personality.processor,"personality_config"):
            return personality.processor.personality_config.config_template.template
        else:
            return {}   
    else:
        return {}  


@router.get("/get_active_personality_settings")
def get_active_personality_settings():
    print("- Retreiving personality settings")
    if lollmsElfServer.personality.processor is not None:
        if hasattr(lollmsElfServer.personality.processor,"personality_config"):
            return lollmsElfServer.personality.processor.personality_config.config_template.template
        else:
            return {}
    else:
        return {}


@router.post("/set_active_personality_settings")
async def set_active_personality_settings(request: Request):
    """
    sets the active personality settings.

    :param request: The HTTP request object.
    :return: A JSON response with the status of the operation.
    """

    try:
        config_data = (await request.json())

        print("- Setting personality settings")
        
        if lollmsElfServer.personality.processor is not None:
            if hasattr(lollmsElfServer.personality.processor,"personality_config"):
                lollmsElfServer.personality.processor.personality_config.update_template(config_data)
                lollmsElfServer.personality.processor.personality_config.config.save_config()
                if lollmsElfServer.config.auto_save:
                    ASCIIColors.info("Saving configuration")
                    lollmsElfServer.config.save_config()
                if lollmsElfServer.personality.processor:
                    lollmsElfServer.personality.processor.settings_updated()
                return {'status':True}
            else:
                return {'status':False}
        else:
            return {'status':False}  
    except Exception as ex:
        trace_exception(ex)
        lollmsElfServer.error(ex)
        return {"status":False,"error":str(ex)}


class PersonalityInfos(BaseModel):
    category:str
    name:str
    language:Optional[str] = None

@router.post("/copy_to_custom_personas")
async def copy_to_custom_personas(data: PersonalityInfos):
    """
    Copies the personality to custom personas so that you can modify it.

    """
    import shutil
    category = data.category
    name = data.name

    if category=="custom_personalities":
        lollmsElfServer.InfoMessage("This persona is already in custom personalities folder")
        return {"status":False}
    else:
        personality_folder = lollmsElfServer.lollms_paths.personalities_zoo_path/f"{category}"/f"{name}"
        destination_folder = lollmsElfServer.lollms_paths.personal_personalities_path
        shutil.copy(personality_folder, destination_folder)
        return {"status":True}

# ------------------------------------------- Interaction with personas ------------------------------------------------
@router.post("/post_to_personality")
async def post_to_personality(request: Request):
    """Post data to a personality"""

    try:
        if hasattr(lollmsElfServer.personality.processor,'handle_request'):
            return await lollmsElfServer.personality.processor.handle_request(request)
        else:
            return {}
    except Exception as ex:
        trace_exception(ex)
        lollmsElfServer.error(ex)
        return {"status":False,"error":str(ex)}
    
