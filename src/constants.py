import os

try:
    from musicdl import musicdl
    MUSICDL_AVAILABLE = True
except ImportError:
    musicdl = None
    MUSICDL_AVAILABLE = False
    print("警告：musicdl 库未安装，请运行 pip install musicdl")

# 来源名称映射 (中文 -> 英文)
SOURCE_MAP_CN_TO_EN = {
    "苹果音乐": "AppleMusicClient",
    "Deezer": "DeezerMusicClient",
    "5sing": "FiveSingMusicClient",
    "Jamendo": "JamendoMusicClient",
    "Joox": "JooxMusicClient",
    "酷我音乐": "KuwoMusicClient",
    "酷狗音乐": "KugouMusicClient",
    "咪咕音乐": "MiguMusicClient",
    "网易云音乐": "NeteaseMusicClient",
    "QQ音乐": "QQMusicClient",
    "千千音乐": "QianqianMusicClient",
    "Qobuz": "QobuzMusicClient",
    "SoundCloud": "SoundCloudMusicClient",
    "StreetVoice": "StreetVoiceMusicClient",
    "汽水音乐": "SodaMusicClient",
    "Spotify": "SpotifyMusicClient",
    "TIDAL": "TIDALMusicClient",
}
SOURCE_MAP_EN_TO_CN = {v: k for k, v in SOURCE_MAP_CN_TO_EN.items()}

# 默认选中的来源
DEFAULT_CHECKED_SOURCES = ["酷我音乐", "酷狗音乐"]
DEFAULT_SPIN_LIMIT = 10
DEFAULT_SAVE_DIR = os.path.join(os.getcwd(), "已下载音乐")

# 现代风格样式表
MODERN_STYLE = """
#CentralWidget { background-color: #f3f4f6; }
QGroupBox { font-size: 11pt; font-weight: bold; color: #1f2937; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; margin-top: 12px; padding-top: 14px; padding-bottom: 6px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #0078d4; }
QCheckBox { padding: 2px; color: #4b5563; }
QCheckBox:hover { color: #0078d4; }
QLineEdit, ModernComboBox, ModernSpinBox { border: 1px solid #d1d5db; border-radius: 6px; padding: 4px 10px; background: #ffffff; min-height: 24px; color: #1f2937; }
QLineEdit:focus, ModernComboBox:focus, ModernSpinBox:focus { border: 1px solid #0078d4; }
ModernComboBox::drop-down { width: 24px; border: none; background: transparent; }
ModernComboBox::down-arrow { image: none; }
ModernComboBox QAbstractItemView { border: 1px solid #d1d5db; border-radius: 6px; background-color: #ffffff; selection-background-color: #e0f2fe; selection-color: #0369a1; outline: none; padding: 2px; }
ModernComboBox QAbstractItemView::item { min-height: 28px; border-radius: 4px; padding-left: 6px; }
ModernSpinBox { padding-right: 22px; }
ModernSpinBox::up-button, ModernSpinBox::down-button { subcontrol-origin: border; width: 20px; border-left: 1px solid transparent; background: transparent; }
ModernSpinBox::up-button { subcontrol-position: top right; border-bottom: 1px solid transparent; border-top-right-radius: 5px; }
ModernSpinBox::down-button { subcontrol-position: bottom right; border-bottom-right-radius: 5px; }
ModernSpinBox::up-button:hover, ModernSpinBox::down-button:hover { background: #f3f4f6; }
ModernSpinBox::up-arrow, ModernSpinBox::down-arrow { image: none; }
QPushButton { border: none; border-radius: 6px; padding: 6px 16px; background-color: #0078d4; color: white; font-weight: bold; font-size: 10pt; }
QPushButton:hover { background-color: #1089e5; }
QPushButton:pressed { background-color: #005a9e; }
QPushButton:disabled { background-color: #9ca3af; color: #f3f4f6; }
QPushButton#SearchBtn { background-color: #10b981; }
QPushButton#SearchBtn:hover { background-color: #059669; }
QTableWidget { border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; alternate-background-color: #f9fafb; color: #374151; selection-background-color: #e0f2fe; selection-color: #0369a1; outline: none; }
QHeaderView::section { background: #f3f4f6; color: #4b5563; font-weight: bold; border: none; border-bottom: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; padding: 6px 8px; }
QTableWidget::item { padding: 2px; border-bottom: 1px solid #f3f4f6; }
QScrollBar:vertical { border: none; background: #f3f4f6; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #d1d5db; min-height: 20px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: #9ca3af; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
"""