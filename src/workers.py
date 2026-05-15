# workers.py
import os
import shutil
import requests
from PySide6.QtCore import QThread, Signal, QRunnable, QObject, QThreadPool, Qt
from PySide6.QtGui import QPixmap
from .constants import MUSICDL_AVAILABLE, musicdl
from .utils import sanitize_filename

if not MUSICDL_AVAILABLE:
    # 占位，避免后面引用出错
    musicdl = None

# ---------- ImageDownloadTask ----------
class ImageWorkerSignals(QObject):
    finished = Signal(int, QPixmap)
    error = Signal(int)

class ImageDownloadTask(QRunnable):
    def __init__(self, row, image_url):
        super().__init__()
        self.row = row
        self.image_url = image_url
        self.signals = ImageWorkerSignals()

    def run(self):
        try:
            if not self.image_url:
                self.signals.error.emit(self.row)
                return
            response = requests.get(self.image_url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                scaled_pixmap = pixmap.scaled(
                    44, 44,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.signals.finished.emit(self.row, scaled_pixmap)
            else:
                self.signals.error.emit(self.row)
        except Exception:
            self.signals.error.emit(self.row)

# ---------- SearchThread ----------
class SearchThread(QThread):
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(int)  # 新增进度信号

    def __init__(self, music_client, keyword, search_type):
        super().__init__()
        self.music_client = music_client
        self.keyword = keyword
        self.search_type = search_type

    def run(self):
        try:
            if self.search_type == "搜索歌曲":
                # 发送开始搜索进度
                self.progress.emit(10)
                results = self.music_client.search(keyword=self.keyword)
                # 发送搜索完成进度
                self.progress.emit(90)
            else:
                self.progress.emit(10)
                results = self.music_client.parseplaylist(self.keyword)
                self.progress.emit(90)
                if not isinstance(results, dict):
                    results = {"歌单": results}

            # 最终完成
            self.progress.emit(100)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

# ---------- DownloadThread ----------
class DownloadThread(QThread):
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, music_client, song_infos, target_dir):
        super().__init__()
        self.music_client = music_client
        self.song_infos = song_infos
        self.target_dir = target_dir

    def _get_val(self, obj, key, default=""):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default) if hasattr(obj, key) else default

    def run(self):
        try:
            downloaded_songs = self.music_client.download(song_infos=self.song_infos)
            success_count = 0

            for song in downloaded_songs:
                save_path = self._get_val(song, "save_path")
                if not save_path or not os.path.exists(save_path):
                    continue

                song_name = self._get_val(song, "song_name", "未知歌曲")
                singers = self._get_val(song, "singers", "未知歌手")
                if isinstance(singers, list):
                    singer = "&".join([str(s) for s in singers])
                else:
                    singer = str(singers)

                album = self._get_val(song, "album", "")
                identifier = self._get_val(song, "identifier", "")

                ext = os.path.splitext(save_path)[1].lstrip(".")
                if not ext:
                    ext = self._get_val(song, "ext", "mp3")

                parts = [song_name, singer]
                if album:
                    parts.append(str(album))
                if identifier:
                    parts.append(str(identifier))

                base_name = sanitize_filename("-".join(parts))
                new_audio_name = f"{base_name}.{ext}"
                new_audio_path = os.path.join(self.target_dir, new_audio_name)

                try:
                    if os.path.exists(new_audio_path):
                        os.remove(new_audio_path)
                    shutil.move(save_path, new_audio_path)
                    success_count += 1
                except Exception as e:
                    print(f"移动音频文件失败 {save_path}: {e}")

                old_lrc_path = os.path.splitext(save_path)[0] + ".lrc"
                if os.path.exists(old_lrc_path):
                    new_lrc_name = f"{base_name}.lrc"
                    new_lrc_path = os.path.join(self.target_dir, new_lrc_name)
                    try:
                        if os.path.exists(new_lrc_path):
                            os.remove(new_lrc_path)
                        shutil.move(old_lrc_path, new_lrc_path)
                    except Exception as e:
                        print(f"移动歌词文件失败: {e}")

            self.finished.emit(success_count)
        except Exception as e:
            self.error.emit(str(e))