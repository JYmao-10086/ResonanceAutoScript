"""路径与默认配置。"""

from __future__ import annotations

import os

# 模板图与坐标逻辑的基准分辨率（picture 资源按此分辨率截取）
BASE_WIDTH = 1920
BASE_HEIGHT = 1080

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

PICTURE_DIR = os.path.join(ROOT_DIR, "picture")
SETTINGS_FILE = os.path.join(ROOT_DIR, "settings.json")
CITIES_XLSX = os.path.join(ROOT_DIR, "城市-商品.xlsx")
ICON_PATH = os.path.join(PICTURE_DIR, "gui_ico.ico")

DEFAULT_ADB_DIR = os.path.join(ROOT_DIR, "adb")
DEFAULT_ADB_EXE = os.path.join(DEFAULT_ADB_DIR, "adb.exe")

# 常见模拟器 ADB 端口
MUMU_PORT = "7555"
LDPLAYER_PORT = "5555"
NOX_PORT = "62001"

# subprocess 隐藏控制台窗口（Windows）
CREATE_NO_WINDOW = 0x08000000

SCREENSHOT_DEVICE_PATH = "/sdcard/screenshot.png"
SCREENSHOT_LOCAL_PATH = os.path.join(PICTURE_DIR, "screenshot.png")
MAP_IMAGE_PATH = os.path.join(PICTURE_DIR, "map.png")


def picture_path(*parts: str) -> str:
    """拼接 picture 目录下的资源路径。"""
    return os.path.join(PICTURE_DIR, *parts)
