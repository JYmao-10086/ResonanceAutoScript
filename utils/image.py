"""图像读写工具。"""

from __future__ import annotations

import numpy as np
import cv2


def cv_imread(file_path: str):
    """支持中文路径的图片读取。"""
    return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
