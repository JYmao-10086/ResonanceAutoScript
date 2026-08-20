"""分辨率适配：模板按 1920x1080，设备坐标按实际分辨率换算。"""

from __future__ import annotations

import re
from typing import Optional, Tuple

import cv2

from config import BASE_HEIGHT, BASE_WIDTH
from state import state


def set_device_resolution(width: int, height: int) -> None:
    """写入设备分辨率，并更新缩放比。"""
    if width <= 0 or height <= 0:
        return
    state.screen_width = width
    state.screen_height = height
    state.scale_x = width / float(BASE_WIDTH)
    state.scale_y = height / float(BASE_HEIGHT)


def parse_wm_size(output: str) -> Optional[Tuple[int, int]]:
    """
    解析 `adb shell wm size` 输出。
    优先 Override size，其次 Physical size。
    """
    override = re.search(r"Override size:\s*(\d+)x(\d+)", output)
    if override:
        return int(override.group(1)), int(override.group(2))
    physical = re.search(r"Physical size:\s*(\d+)x(\d+)", output)
    if physical:
        return int(physical.group(1)), int(physical.group(2))
    plain = re.search(r"(\d+)x(\d+)", output)
    if plain:
        return int(plain.group(1)), int(plain.group(2))
    return None


def design_to_device(x: float | int | str, y: float | int | str) -> Tuple[int, int]:
    """基准坐标（1920x1080）-> 设备坐标。"""
    return (
        int(round(float(x) * state.scale_x)),
        int(round(float(y) * state.scale_y)),
    )


def resolution_label() -> str:
    return (
        f"{state.screen_width}x{state.screen_height}"
        f"（相对 {BASE_WIDTH}x{BASE_HEIGHT} "
        f"缩放 {state.scale_x:.3f}x / {state.scale_y:.3f}y）"
    )


def cv_imwrite(file_path: str, image) -> None:
    """支持中文路径写图。"""
    ext = "." + file_path.rsplit(".", 1)[-1] if "." in file_path else ".png"
    ok, buf = cv2.imencode(ext, image)
    if not ok:
        raise RuntimeError(f"写图失败: {file_path}")
    buf.tofile(file_path)


def normalize_screenshot_to_base(file_path: str) -> Tuple[int, int]:
    """
    根据截图更新设备分辨率，并将截图缩放到基准分辨率后写回。
    返回截图原始 (width, height)。
    """
    from utils.image import cv_imread

    image = cv_imread(file_path)
    if image is None:
        raise RuntimeError(f"无法读取截图: {file_path}")

    height, width = image.shape[:2]
    set_device_resolution(width, height)

    if width != BASE_WIDTH or height != BASE_HEIGHT:
        interpolation = cv2.INTER_AREA if (width > BASE_WIDTH or height > BASE_HEIGHT) else cv2.INTER_LINEAR
        image = cv2.resize(image, (BASE_WIDTH, BASE_HEIGHT), interpolation=interpolation)
        cv_imwrite(file_path, image)

    return width, height
