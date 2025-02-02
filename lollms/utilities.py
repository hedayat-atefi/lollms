
######
# Project       : lollms
# File          : utilities.py
# Author        : ParisNeo with the help of the community
# license       : Apache 2.0
# Description   : 
# This file contains utilities functions that can be used by any
# module.
######
from ascii_colors import ASCIIColors, trace_exception
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from pathlib import Path
import json
import re
import subprocess
import gc

from typing import List

from PIL import Image
import requests
from io import BytesIO
import base64
import importlib
import yaml

import asyncio

import ctypes
import io
import urllib
import os
import sys


def yes_or_no_input(prompt):
    while True:
        user_input = input(prompt + " (yes/no): ").lower()
        if user_input == 'yes':
            return True
        elif user_input == 'no':
            return False
        else:
            print("Please enter 'yes' or 'no'.")

def show_yes_no_dialog(title, text):
    import tkinter as tk
    from tkinter import messagebox
    # Create a new Tkinter root window and hide it
    root = tk.Tk()
    root.withdraw()

    # Make the window appear on top
    root.attributes('-topmost', True)
    
    # Show the dialog box
    result = messagebox.askyesno(title, text)

    # Destroy the root window
    root.destroy()

    return result

def is_linux():
    return sys.platform.startswith("linux")


def is_windows():
    return sys.platform.startswith("win")


def is_macos():
    return sys.platform.startswith("darwin")

def run_cmd(cmd, assert_success=False, environment=False, capture_output=False, env=None):
    script_dir = os.getcwd()
    conda_env_path = os.path.join(script_dir, "installer_files", "env")
    # Use the conda environment
    if environment:
        if is_windows():
            conda_bat_path = os.path.join(script_dir, "installer_files", "conda", "condabin", "conda.bat")
            cmd = "\"" + conda_bat_path + "\" activate \"" + conda_env_path + "\" >nul && " + cmd
        else:
            conda_sh_path = os.path.join(script_dir, "installer_files", "conda", "etc", "profile.d", "conda.sh")
            cmd = ". \"" + conda_sh_path + "\" && conda activate \"" + conda_env_path + "\" && " + cmd

    # Run shell commands
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, env=env)

    # Assert the command ran successfully
    if assert_success and result.returncode != 0:
        print("Command '" + cmd + "' failed with exit status code '" + str(result.returncode) + "'.\n\nExiting now.\nTry running the start/update script again.")
        sys.exit(1)

    return result

def file_path_to_url(file_path):
    """
    This function takes a file path as an argument and converts it into a URL format. It first removes the initial part of the file path until the "outputs" string is reached, then replaces backslashes with forward slashes and quotes each segment with urllib.parse.quote() before joining them with forward slashes to form the final URL.

    :param file_path: str, the file path in the format of a Windows system
    :return: str, the converted URL format of the given file path
    """

    url = "/"+file_path[file_path.index("outputs"):].replace("\\","/")
    return "/".join([urllib.parse.quote(p, safe="") for p in url.split("/")])


def discussion_path_to_url(file_path:str|Path)->str:
    """
    This function takes a file path as an argument and converts it into a URL format. It first removes the initial part of the file path until the "outputs" string is reached, then replaces backslashes with forward slashes and quotes each segment with urllib.parse.quote() before joining them with forward slashes to form the final URL.

    :param file_path: str, the file path in the format of a Windows system
    :return: str, the converted URL format of the given file path
    """
    file_path = str(file_path)
    url = "/"+file_path[file_path.index("discussion_databases"):].replace("\\","/").replace("discussion_databases","discussions")
    return "/".join([urllib.parse.quote(p, safe="") for p in url.split("/")])


def is_asyncio_loop_running():
    """
    # This function checks if an AsyncIO event loop is currently running. If an event loop is running, it returns True. If not, it returns False.
    :return: bool, indicating whether or not an AsyncIO event loop is currently running
    """
    try:
        return asyncio.get_event_loop().is_running()
    except RuntimeError:  # This gets raised if there's no running event loop
        return False

def run_async(func):
    """
    run_async(func) -> None

    Utility function to run async functions in sync environment. Takes an async function as input and runs it within an async context.

    Parameters:
    func (function): The async function to run.

    Returns:
    None: Nothing is returned since the function is meant to perform side effects.
    """
    if is_asyncio_loop_running():
        # We're in a running event loop, so we can call the function with asyncio.create_task
        asyncio.create_task(func())
    else: 
        # We're not in a running event loop, so we need to create one and run the function in it
        try:
            asyncio.run(func()) 
        except:
            func()


def terminate_thread(thread):
    """ 
    This function is used to terminate a given thread if it's currently running. If the thread is not alive, an informational message will be displayed and the function will return without raising any error. Otherwise, it sets the thread's exception to `SystemExit` using `ctypes`, which causes the thread to exit. The function collects the garbage after terminating the thread, and raises a `SystemError` if it fails to do so.
    :param thread: thread object to be terminated
    :return: None if the thread was successfully terminated or an error is raised
    :raises SystemError: if the thread could not be terminated 
    """    
    if thread:
        if not thread.is_alive():
            ASCIIColors.yellow("Thread not alive")
            return

        thread_id = thread.ident
        exc = ctypes.py_object(SystemExit)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, exc)
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, None)
            del thread
            gc.collect()
            raise SystemError("Failed to terminate the thread.")
        else:
            ASCIIColors.yellow("Canceled successfully")

def convert_language_name(language_name):
    """
    Convert a language name string to its corresponding ISO 639-1 code.
    If the given language name is not supported, returns "unsupported".

    Parameters:
    - language_name (str): A lowercase and dot-free string representing the name of a language.

    Returns:
    - str: The corresponding ISO 639-1 code for the given language name or "unsupported" if it's not supported.
    """    
    # Remove leading and trailing spaces
    language_name = language_name.strip()
    
    # Convert to lowercase
    language_name = language_name.lower().replace(".","")
    
    # Define a dictionary mapping language names to their codes
    language_codes = { 
                      "english": "en", "spanish": "es", "french": "fr", "german": "de",
                      "italian": "it", "portuguese": "pt", "russian": "ru", "mandarin": "zh-CN",
                      "korean": "ko", "japanese": "ja", "dutch": "nl", "polish": "pl",
                      "hindi": "hi", "arabic": "ar", "bengali": "bn", "swedish": "sv", "thai": "th", "vietnamese": "vi"
                    }
    
    # Return the corresponding language code if found, or None otherwise
    return language_codes.get(language_name,"en")


# Function to encode the image
def encode_image(image_path, max_image_width=-1):
    image = Image.open(image_path)
    width, height = image.size

    # Check and convert image format if needed
    if image.format not in ['PNG', 'JPEG', 'GIF', 'WEBP']:
        image = image.convert('JPEG')


    if max_image_width != -1 and width > max_image_width:
        ratio = max_image_width / width
        new_width = max_image_width
        new_height = int(height * ratio)
        f = image.format
        image = image.resize((new_width, new_height))
        image.format = f


    # Save the image to a BytesIO object
    byte_arr = io.BytesIO()
    image.save(byte_arr, format=image.format)
    byte_arr = byte_arr.getvalue()

    return base64.b64encode(byte_arr).decode('utf-8')

def load_config(file_path):
    with open(file_path, 'r', encoding='utf-8') as stream:
        config = yaml.safe_load(stream)

    return config


def save_config(config, filepath):
    with open(filepath, "w") as f:
        yaml.dump(config, f)


def load_image(image_file):
    s_image_file = str(image_file)
    if s_image_file.startswith('http://') or s_image_file.startswith('https://'):
        response = requests.get(s_image_file)
        image = Image.open(BytesIO(response.content)).convert('RGB')
    else:
        image = Image.open(s_image_file).convert('RGB')
    return image

def load_image_from_base64(image):
    return Image.open(BytesIO(base64.b64decode(image)))


def expand2square(pil_img, background_color):
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result


def add_period(text):
    """
    Adds a period at the end of each line in the given text, except for empty lines.

    Args:
        text (str): The input text.

    Returns:
        str: The preprocessed text with a period added at the end of each line that doesn't already have one.
    """
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        if line.strip():  # Check if line is not empty
            if line[-1] != '.':
                line += '.'
        processed_lines.append(line)
    
    processed_text = '\n'.join(processed_lines)
    return processed_text


def find_first_available_file_index(folder_path, prefix, extension=""):
    """
    Finds the first available file index in a folder with files that have a prefix and an optional extension.
    
    Args:
        folder_path (str): The path to the folder.
        prefix (str): The file prefix.
        extension (str, optional): The file extension (including the dot). Defaults to "".
    
    Returns:
        int: The first available file index.
    """
    # Create a Path object for the folder
    folder = Path(folder_path)
    
    # Get a list of all files in the folder
    files = folder.glob(f'{prefix}*'+extension)
    
    # Initialize the first available number
    available_number = 1
    
    # Iterate through the files
    while True:
        f = folder/f"{prefix}{available_number}{extension}"
        if f.exists():
            available_number += 1
        # If the file number is greater than the available number, break the loop
        else:
            return available_number




# Prompting tools
def detect_antiprompt(text:str, anti_prompts=["!@>"]) -> bool:
    """
    Detects if any of the antiprompts in self.anti_prompts are present in the given text.
    Used for the Hallucination suppression system

    Args:
        text (str): The text to check for antiprompts.

    Returns:
        bool: True if any antiprompt is found in the text (ignoring case), False otherwise.
    """
    for prompt in anti_prompts:
        if prompt.lower() in text.lower():
            return prompt.lower()
    return None


def remove_text_from_string(string, text_to_find):
    """
    Removes everything from the first occurrence of the specified text in the string (case-insensitive).

    Parameters:
    string (str): The original string.
    text_to_find (str): The text to find in the string.

    Returns:
    str: The updated string.
    """
    index = string.lower().find(text_to_find.lower())

    if index != -1:
        string = string[:index]

    return string


# Pytorch and cuda tools
def check_torch_version(min_version, min_cuda_versio=12):
    import torch

    if "+" in torch.__version__ and int(torch.__version__.split("+")[-1][2:4])<min_cuda_versio:
        return False

    # Extract torch version from __version__ attribute with regular expression
    current_version_float = float('.'.join(torch.__version__.split(".")[:2]))
    # Check if the current version meets or exceeds the minimum required version
    return current_version_float >= min_version


def reinstall_pytorch_with_cuda():
    try:
        import conda.cli
        ASCIIColors.info("Installing cuda 12.1.1") # -c nvidia/label/cuda-12.1.1 -c nvidia -c conda-forge
        result = conda.cli.main("install", "-c", "nvidia/label/cuda-12.1.1", "-c", "nvidia", "-c", "conda-forge", "cuda-toolkit","-y")
    except Exception as ex:
        ASCIIColors.error(ex)
    try:
        ASCIIColors.info("Installing ninja") # -c nvidia/label/cuda-12.1.1 -c nvidia -c conda-forge
        result = conda.cli.main("install", "-c", "nvidia/label/cuda-12.1.1", "-c", "nvidia", "-c", "conda-forge", "ninja", "-y")
    except Exception as ex:
        ASCIIColors.error(ex)
    try:
        ASCIIColors.info("Installing cuda compiler") # -c nvidia/label/cuda-12.1.1 -c nvidia -c conda-forge
        result = conda.cli.main("install", "-c", "nvidia/label/cuda-12.1.1", "-c", "nvidia", "-c", "conda-forge", "cuda-compiler", "-y")
    except Exception as ex:
        ASCIIColors.error(ex)
    try:
        ASCIIColors.info("Installing pytorch 2.1.1")
        result = subprocess.run(["pip", "install", "--upgrade", "torch", "torchvision", "torchaudio", "--no-cache-dir", "--index-url", "https://download.pytorch.org/whl/cu121"])
    except Exception as ex:
        ASCIIColors.error(ex)
    if result.returncode != 0:
        ASCIIColors.warning("Couldn't find Cuda build tools on your PC. Reverting to CPU.")
        result = subprocess.run(["pip", "install", "--upgrade", "torch", "torchvision", "torchaudio", "--no-cache-dir"])
        if result.returncode != 0:
            ASCIIColors.error("Couldn't install pytorch !!")
        else:
            ASCIIColors.error("Pytorch installed successfully!!")


def reinstall_pytorch_with_rocm():
    result = subprocess.run(["pip", "install", "--upgrade", "torch", "torchvision", "torchaudio", "--no-cache-dir", "--index-url", "https://download.pytorch.org/whl/rocm5.6"])
    if result.returncode != 0:
        ASCIIColors.warning("Couldn't find Cuda build tools on your PC. Reverting to CPU.")
        result = subprocess.run(["pip", "install", "--upgrade", "torch", "torchvision", "torchaudio", "--no-cache-dir"])
        if result.returncode != 0:
            ASCIIColors.error("Couldn't install pytorch !!")
        else:
            ASCIIColors.error("Pytorch installed successfully!!")
            
            

def reinstall_pytorch_with_cpu():
    result = subprocess.run(["pip", "install", "--upgrade", "torch", "torchvision", "torchaudio", "--no-cache-dir"])
    if result.returncode != 0:
        ASCIIColors.warning("Couldn't find Cuda build tools on your PC. Reverting to CPU.")
        result = subprocess.run(["pip", "install", "--upgrade", "torch", "torchvision", "torchaudio", "--no-cache-dir"])
        if result.returncode != 0:
            ASCIIColors.error("Couldn't install pytorch !!")
        else:
            ASCIIColors.error("Pytorch installed successfully!!")     


def check_and_install_torch(enable_gpu:bool, version:float=2.1):
    if enable_gpu:
        ASCIIColors.yellow("This installation has enabled GPU support. Trying to install with GPU support")
        ASCIIColors.info("Checking pytorch")
        try:
            import torch
            import torchvision
            if torch.cuda.is_available():
                ASCIIColors.success(f"CUDA is supported.\nCurrent version is {torch.__version__}.")
                if not check_torch_version(version):
                    ASCIIColors.yellow("Torch version is old. Installing new version")
                    reinstall_pytorch_with_cuda()
                else:
                    ASCIIColors.yellow("Torch OK")
            else:
                ASCIIColors.warning("CUDA is not supported. Trying to reinstall PyTorch with CUDA support.")
                reinstall_pytorch_with_cuda()
        except Exception as ex:
            ASCIIColors.info("Pytorch not installed. Reinstalling ...")
            reinstall_pytorch_with_cuda()    
    else:
        try:
            import torch
            import torchvision
            if check_torch_version(version):
                ASCIIColors.warning("Torch version is too old. Trying to reinstall PyTorch with CUDA support.")
                reinstall_pytorch_with_cpu()
        except Exception as ex:
            ASCIIColors.info("Pytorch not installed. Reinstalling ...")
            reinstall_pytorch_with_cpu() 
    

class NumpyEncoderDecoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return {'__numpy_array__': True, 'data': obj.tolist()}
        return super(NumpyEncoderDecoder, self).default(obj)

    @staticmethod
    def as_numpy_array(dct):
        if '__numpy_array__' in dct:
            return np.array(dct['data'])
        return dct


def git_pull(folder_path):
    try:
        # Change the current working directory to the desired folder
        subprocess.run(["git", "checkout", folder_path], check=True, cwd=folder_path)
        # Run 'git pull' in the specified folder
        subprocess.run(["git", "pull"], check=True, cwd=folder_path)
        print("Git pull successful in", folder_path)
    except subprocess.CalledProcessError as e:
        print("Error occurred while executing Git pull:", e)
        # Handle any specific error handling here if required
class AdvancedGarbageCollector:
    @staticmethod
    def hardCollect(obj):
        """
        Remove a reference to the specified object and attempt to collect it.

        Parameters:
        - obj: The object to be collected.

        This method first identifies all the referrers (objects referencing the 'obj')
        using Python's garbage collector (gc.get_referrers). It then iterates through
        the referrers and attempts to break their reference to 'obj' by setting them
        to None. Finally, it deletes the 'obj' reference.

        Note: This method is designed to handle circular references and can be used
        to forcefully collect objects that might not be collected automatically.

        """
        if obj is None:
            return
        all_referrers = gc.get_referrers(obj)
        for referrer in all_referrers:
            try:
                if isinstance(referrer, (list, tuple, dict, set)):
                    if isinstance(referrer, list):
                        if obj in referrer:
                            referrer.remove(obj)
                    elif isinstance(referrer, dict):
                        new_dict = {}
                        for key, value in referrer.items():
                            if value != obj:
                                new_dict[key] = value
                        referrer.clear()
                        referrer.update(new_dict)
                    elif isinstance(referrer, set):
                        if obj in referrer:
                            referrer.remove(obj)
            except:
                ASCIIColors.warning("Couldn't remove object from referrer")
        del obj

    @staticmethod
    def safeHardCollect(variable_name, instance=None):
        """
        Safely remove a reference to a variable and attempt to collect its object.

        Parameters:
        - variable_name: The name of the variable to be collected.
        - instance: An optional instance (object) to search for the variable if it
          belongs to an object.

        This method provides a way to safely break references to a variable by name.
        It first checks if the variable exists either in the local or global namespace
        or within the provided instance. If found, it calls the 'hardCollect' method
        to remove the reference and attempt to collect the associated object.

        """
        if instance is not None:
            if hasattr(instance, variable_name):
                obj = getattr(instance, variable_name)
                AdvancedGarbageCollector.hardCollect(obj)
            else:
                print(f"The variable '{variable_name}' does not exist in the instance.")
        else:
            if variable_name in locals():
                obj = locals()[variable_name]
                AdvancedGarbageCollector.hardCollect(obj)
            elif variable_name in globals():
                obj = globals()[variable_name]
                AdvancedGarbageCollector.hardCollect(obj)
            else:
                print(f"The variable '{variable_name}' does not exist in the local or global namespace.")

    @staticmethod
    def safeHardCollectMultiple(variable_names, instance=None):
        """
        Safely remove references to multiple variables and attempt to collect their objects.

        Parameters:
        - variable_names: A list of variable names to be collected.
        - instance: An optional instance (object) to search for the variables if they
          belong to an object.

        This method iterates through a list of variable names and calls 'safeHardCollect'
        for each variable, effectively removing references and attempting to collect
        their associated objects.

        """
        for variable_name in variable_names:
            AdvancedGarbageCollector.safeHardCollect(variable_name, instance)

    @staticmethod
    def collect():
        """
        Perform a manual garbage collection using Python's built-in 'gc.collect' method.

        This method triggers a manual garbage collection, attempting to clean up
        any unreferenced objects in memory. It can be used to free up memory and
        resources that are no longer in use.

        """
        gc.collect()


class PackageManager:
    @staticmethod
    def install_package(package_name):
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package_name])
        
    @staticmethod
    def check_package_installed(package_name):
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False
        
    @staticmethod
    def safe_import(module_name, library_name=None):
        if not PackageManager.check_package_installed(module_name):
            print(f"{module_name} module not found. Installing...")
            if library_name:
                PackageManager.install_package(library_name)
            else:
                PackageManager.install_package(module_name)
        globals()[module_name] = importlib.import_module(module_name)
        print(f"{module_name} module imported successfully.")


class GitManager:
    @staticmethod
    def git_pull(folder_path):
        try:
            # Change the current working directory to the desired folder
            subprocess.run(["git", "checkout", folder_path], check=True, cwd=folder_path)
            # Run 'git pull' in the specified folder
            subprocess.run(["git", "pull"], check=True, cwd=folder_path)
            print("Git pull successful in", folder_path)
        except subprocess.CalledProcessError as e:
            print("Error occurred while executing Git pull:", e)
            # Handle any specific error handling here if required

class File64BitsManager:

    @staticmethod
    def raw_b64_img(image) -> str:
        try:
            from PIL import Image, PngImagePlugin
            import io
            import base64
        except:
            PackageManager.install_package("Pillow")
            from PIL import Image
            import io
            import base64

        # XXX controlnet only accepts RAW base64 without headers
        with io.BytesIO() as output_bytes:
            metadata = None
            for key, value in image.info.items():
                if isinstance(key, str) and isinstance(value, str):
                    if metadata is None:
                        metadata = PngImagePlugin.PngInfo()
                    metadata.add_text(key, value)
            image.save(output_bytes, format="PNG", pnginfo=metadata)

            bytes_data = output_bytes.getvalue()

        return str(base64.b64encode(bytes_data), "utf-8")


    @staticmethod
    def img2b64(image) -> str:
        return "data:image/png;base64," + File64BitsManager.raw_b64_img(image)    

    @staticmethod
    def b642img(b64img) -> str:
        try:
            from PIL import Image, PngImagePlugin
            import io
            import base64
        except:
            PackageManager.install_package("Pillow")
            from PIL import Image
            import io
            import base64        
        image_data = re.sub('^data:image/.+;base64,', '', b64img)
        return Image.open(io.BytesIO(base64.b64decode(image_data)))  

    @staticmethod
    def get_supported_file_extensions_from_base64(b64data):
        # Extract the file extension from the base64 data
        data_match = re.match(r'^data:(.*?);base64,', b64data)
        if data_match:
            mime_type = data_match.group(1)
            extension = mime_type.split('/')[-1]
            return extension
        else:
            raise ValueError("Invalid base64 data format.")
        
    @staticmethod
    def extract_content_from_base64(b64data):
        # Split the base64 data at the comma separator
        header, content = b64data.split(',', 1)

        # Extract only the content part and remove any white spaces and newlines
        content = content.strip()

        return content

    @staticmethod
    def b642file(b64data, filename):
        import base64   
        # Extract the file extension from the base64 data
        
        
        # Save the file with the determined extension
        with open(filename, 'wb') as file:
            file.write(base64.b64decode(File64BitsManager.extract_content_from_base64(b64data)))

        return filename
class TFIDFLoader:
    @staticmethod
    def create_vectorizer_from_dict(tfidf_info):
        vectorizer = TfidfVectorizer(**tfidf_info['params'])
        vectorizer.vocabulary_ = tfidf_info['vocabulary']
        vectorizer.idf_ = [tfidf_info['idf_values'][feature] for feature in vectorizer.get_feature_names()]
        return vectorizer

    @staticmethod
    def create_dict_from_vectorizer(vectorizer):
        tfidf_info = {
            "vocabulary": vectorizer.vocabulary_,
            "idf_values": dict(zip(vectorizer.get_feature_names(), vectorizer.idf_)),
            "params": vectorizer.get_params()
        }
        return tfidf_info
    
class DocumentDecomposer:
    @staticmethod
    def clean_text(text):
        # Remove extra returns and leading/trailing spaces
        text = text.replace('\r', '').strip()
        return text

    @staticmethod
    def split_into_paragraphs(text):
        # Split the text into paragraphs using two or more consecutive newlines
        paragraphs = [p+"\n" for p in re.split(r'\n{2,}', text)]
        return paragraphs

    @staticmethod
    def tokenize_sentences(paragraph):
        # Custom sentence tokenizer using simple regex-based approach
        sentences = [s+"." for s in paragraph.split(".")]
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
        return sentences

    @staticmethod
    def decompose_document(text, max_chunk_size, overlap_size, tokenize, detokenize):
        cleaned_text = DocumentDecomposer.clean_text(text)
        paragraphs = DocumentDecomposer.split_into_paragraphs(cleaned_text)

        # List to store the final clean chunks
        clean_chunks = []

        current_chunk = []  # To store the current chunk being built
        l=0
        for paragraph in paragraphs:
            # Tokenize the paragraph into sentences
            sentences = DocumentDecomposer.tokenize_sentences(paragraph)

            for sentence in sentences:
                # If adding the current sentence to the chunk exceeds the max_chunk_size,
                # we add the current chunk to the list of clean chunks and start a new chunk
                tokens = tokenize(sentence)
                nb_tokens = len(tokens)
                if nb_tokens>max_chunk_size:
                    while nb_tokens>max_chunk_size:
                        current_chunk += tokens[:max_chunk_size-l-1]
                        clean_chunks.append(current_chunk)
                        tokens = tokens[max_chunk_size-l-1-overlap_size:]
                        nb_tokens -= max_chunk_size-l-1-overlap_size
                        l=0
                        current_chunk = current_chunk[-overlap_size:]
                else:
                    if l + nb_tokens + 1 > max_chunk_size:

                        clean_chunks.append(current_chunk)
                        if overlap_size==0:
                            current_chunk = []
                        else:
                            current_chunk = current_chunk[-overlap_size:]
                        l=0

                    # Add the current sentence to the chunk
                    current_chunk += tokens
                    l += nb_tokens

        # Add the remaining chunk from the paragraph to the clean_chunks
        if current_chunk:
            clean_chunks.append(current_chunk)
            current_chunk = ""

        return clean_chunks
    
class PromptReshaper:
    def __init__(self, template:str):
        self.template = template
    def replace(self, placeholders:dict)->str:
        template = self.template
        # Calculate the number of tokens for each placeholder
        for placeholder, text in placeholders.items():
            template = template.replace(placeholder, text)
        return template
    def build(self, placeholders:dict, tokenize, detokenize, max_nb_tokens:int, place_holders_to_sacrifice:list=[])->str:
        # Tokenize the template without placeholders
        template_text = self.template
        template_tokens = tokenize(template_text)
        
        # Calculate the number of tokens in the template without placeholders
        template_tokens_count = len(template_tokens)
        
        # Calculate the number of tokens for each placeholder
        placeholder_tokens_count = {}
        all_count = template_tokens_count
        for placeholder, text in placeholders.items():
            text_tokens = tokenize(text)
            placeholder_tokens_count[placeholder] = len(text_tokens)
            all_count += placeholder_tokens_count[placeholder]

        def fill_template(template, data):
            for key, value in data.items():
                placeholder = "{{" + key + "}}"
                n_text_tokens = len(tokenize(template))
                if key in place_holders_to_sacrifice:
                    n_remaining = max_nb_tokens - n_text_tokens
                    t_value = tokenize(value)
                    n_value = len(t_value)
                    if n_value<n_remaining:
                        template = template.replace(placeholder, value)
                    else:
                        value = detokenize(t_value[-n_remaining:])
                        template = template.replace(placeholder, value)
                        
                else:
                    template = template.replace(placeholder, value)
            return template
        
        return fill_template(self.template, placeholders)



class LOLLMSLocalizer:
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def localize(self, input_string):
        def replace(match):
            key = match.group(1)
            return self.dictionary.get(key, match.group(0))
        
        import re
        pattern = r'@<([^>]+)>@'
        localized_string = re.sub(pattern, replace, input_string)
        return localized_string


class File_Path_Generator:
    @staticmethod
    def generate_unique_file_path(folder_path, file_base_name, file_extension):
        folder_path = Path(folder_path)
        index = 0
        while True:
            # Construct the full file path with the current index
            file_name = f"{file_base_name}_{index}.{file_extension}"
            full_file_path = folder_path / file_name
            
            # Check if the file already exists in the folder
            if not full_file_path.exists():
                return full_file_path
            
            # If the file exists, increment the index and try again
            index += 1
