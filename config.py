"""路径与默认配置。"""

from __future__ import annotations

import os
import sys


def _app_root() -> str:
    """源码运行取项目根；封装 exe 取可执行文件所在目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


# 模板图与坐标逻辑的基准分辨率（picture 资源按此分辨率截取）
BASE_WIDTH = 1920
BASE_HEIGHT = 1080

# 项目根目录
ROOT_DIR = _app_root()

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

# OCR 模型（PP-OCRv5 中文，RapidOCR 加载）
MODELS_DIR = os.path.join(ROOT_DIR, "models")
OCR_MODEL_DIR = os.path.join(MODELS_DIR, "ppocr_v5-zh_cn")
OCR_DET_MODEL = os.path.join(OCR_MODEL_DIR, "det.onnx")
OCR_REC_MODEL = os.path.join(OCR_MODEL_DIR, "rec.onnx")
OCR_KEYS_PATH = os.path.join(OCR_MODEL_DIR, "keys.txt")
# OCR 文字识别最低置信度
OCR_TEXT_SCORE = 0.5


# 地图城市坐标（picture/map.png）
MAP_CITY_COORDS = {
    "7号自由港": (2552, 1232),
    "云岫桥基地": (4857, 856),
    "修格里城": (3554, 1056),
    "塔图站": (5006, 2157),
    "岚心城": (6507, 382),
    "曼德矿场": (4030, 1357),
    "栖羽站": (5906, 382),
    "武林源": (129, 1008),
    "汇流塔": (1901, 2709),
    "海角城": (2301, 2709),
    "淘金乐园": (4181, 1782),
    "澄明数据中心": (3130, 883),
    "荒原站": (4255, 1056),
    "贡露城": (3305, 2308),
    "远星大桥": (2954, 2308),
    "铁盟哨站": (3881, 1056),
    "阿妮塔发射中心": (1803, 1857),
    "阿妮塔战备工厂": (2803, 1356),
    "阿妮塔能源研究所": (2475, 1908),
    "黑月游乐城": (2655, 507),
}

# 地图滑动参数
MAP_SWIPE_MIDDLE_RATIO = 0.75
MAP_SWIPE_MAX_RATIO = 0.75
MAP_SWIPE_CENTER_X = BASE_WIDTH // 2
MAP_SWIPE_CENTER_Y = BASE_HEIGHT // 2
MAP_SWIPE_MAX_WIDTH = BASE_WIDTH * MAP_SWIPE_MIDDLE_RATIO * MAP_SWIPE_MAX_RATIO / 2
MAP_SWIPE_MAX_HEIGHT = BASE_HEIGHT * MAP_SWIPE_MIDDLE_RATIO * MAP_SWIPE_MAX_RATIO / 2
MAP_SWIPE_HOLD_DELAY = 1.0
MAP_SWIPE_DURATION = 500
MAP_SWIPE_SETTLE_DELAY = 1.0
EXCHANGE_TAP_OFFSET_Y = 120
TOW_TIMES_BOX = (1263, 410, 1443, 580)
RUBBISH_PICK_TAP = (1160, 666)
RUBBISH_PICK_INTERVAL = 0.5


def picture_path(*parts: str) -> str:

    """拼接 picture 目录下的资源路径。"""
    return os.path.join(PICTURE_DIR, *parts)
