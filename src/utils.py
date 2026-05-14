import re

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", str(filename))

def get_file_format(song_info):
    for field in ["format", "ext", "file_format", "type"]:
        if song_info.get(field):
            return str(song_info[field]).upper()
    url = song_info.get("download_url", "").lower()
    for ext in ["mp3", "flac", "wav", "m4a", "aac"]:
        if f".{ext}" in url:
            return ext.upper()
    return "未知"

def get_album_image_url(song_info):
    for field in [
        "cover", "album_cover", "pic", "picture", "img", "image",
        "album_img", "album_pic", "cover_url", "pic_url"
    ]:
        url = str(song_info.get(field, ""))
        if url.startswith("http"):
            return url
    return ""