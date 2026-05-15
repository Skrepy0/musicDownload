import json
from .constants import CONFIG_PATH, DEFAULT_CHECKED_SOURCES, DEFAULT_SPIN_LIMIT
config={}
checked_sources = []
spin_limit=0
try:
    with open(CONFIG_PATH,'r',encoding='utf-8') as f:
        config = json.load(f)
except:
    pass

try:
    checked_sources = config["checked_sources"]
except:
    checked_sources = DEFAULT_CHECKED_SOURCES
try:
    spin_limit = config["spin_limit"]
except:
    spin_limit = DEFAULT_SPIN_LIMIT
def save_config():
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f)
    except:
        print("写入失败!")
def get_download_path():
    try:
        return config["download_path"]
    except:
        return "已下载音乐"

def set_download_path(path):
    config["download_path"]=path
    save_config()
def get_checked_sources():
    try:
        return checked_sources
    except:
        return DEFAULT_CHECKED_SOURCES
def set_checked_sources(list):
    checked_sources=list
    config["checked_sources"]=checked_sources
    save_config()

def get_spin_limit():
    try:
        return spin_limit
    except:
        return DEFAULT_SPIN_LIMIT

def set_spin_limit(val):
    spin_limit = val
    config["spin_limit"] = spin_limit
    save_config()
