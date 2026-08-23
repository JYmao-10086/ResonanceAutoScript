"""图标模板匹配 + OCR 文字识别的混合识别。"""

from __future__ import annotations

from typing import List, Optional, Union

import cv2

from config import picture_path
from utils.image import cv_imread
from . import ocr

# 需要图片识别的“图标”类名称；其余名称一律走 OCR 文字识别。
# 城市名、交易所（只匹配“交易所”三字）、选项按钮、商品名等文字均走 OCR。
IMAGE_NAMES = {
    "screenshot",  # 大地图上定位当前视野（特殊用法，匹配整张截图）
    "+1",  # 数量 +1 图标按钮
    "空货仓",  # 仓库空置状态图
    "主界面",  # 返回主界面按钮（图标）
    "里程点数",  # 拖车支付选项（图标）
}


def _is_image_name(name: str) -> bool:
    """去掉目录前缀后判断是否属于图片识别的图标。"""
    return name.rsplit("/", 1)[-1] in IMAGE_NAMES


def match_template(
    name: str,
    threshold: float = 0.9,
    base: str = "screenshot",
    cut: Optional[List[int]] = None,
) -> Union[List[int], bool]:
    """在 base 图中识别 picture/{name}.png 对应的内容。

    图标类（IMAGE_NAMES）用模板匹配；城市名、交易所、选项、商品名等文字用 OCR。
    成功返回中心点 [x, y]，失败返回 False。
    OCR 路径忽略 threshold：文字按精确匹配，最低置信度见 OCR_TEXT_SCORE。
    """
    if _is_image_name(name):
        return _match_image(name, threshold, base, cut)
    return _match_text(name, base)


def _match_image(
    name: str,
    threshold: float = 0.9,
    base: str = "screenshot",
    cut: Optional[List[int]] = None,
) -> Union[List[int], bool]:
    if cut is None:
        cut = [0, 0]

    image = cv_imread(picture_path(f"{base}.png"))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    template = cv_imread(picture_path(f"{name}.png"))
    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    theight, twidth = template.shape[:2]
    template = template[cut[1] : theight - cut[1], cut[0] : twidth - cut[0]]
    theight, twidth = template.shape[:2]

    # 多尺度匹配，适配不同分辨率下 UI 缩放差异
    best = None
    for scale in (0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0):
        nw = max(4, int(round(twidth * scale)))
        nh = max(4, int(round(theight * scale)))
        if nw >= image.shape[1] or nh >= image.shape[0]:
            continue
        interp = cv2.INTER_AREA if scale <= 1.0 else cv2.INTER_CUBIC
        scaled = cv2.resize(template, (nw, nh), interpolation=interp)
        result = cv2.matchTemplate(image, scaled, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if best is None or max_val > best[0]:
            best = (max_val, max_loc, nw, nh)

    if best is None:
        return False
    max_val, max_loc, nw, nh = best
    print(f"开始匹配：{name}，最优 {max_val:.3f} @ {nw}x{nh}")
    if max_val > threshold:
        return [nw // 2 + max_loc[0], nh // 2 + max_loc[1]]
    return False


def _text_target(name: str) -> str:
    """取要识别的文字；交易所只保留“交易所”，去掉前面地名。"""
    text = name.rsplit("/", 1)[-1]
    if text.endswith("交易所"):
        return "交易所"
    return text


def _match_text(name: str, base: str) -> Union[List[int], bool]:
    """OCR 识别 base 图中的文字并返回目标文字的中心点。"""
    target = _text_target(name)
    contains = target == "交易所"
    items = ocr.ocr_image_path(picture_path(f"{base}.png"), high_res=(base == "map"))
    center = ocr.find_text(items, target, contains=contains)
    if center is None:
        return False
    return [int(center[0]), int(center[1])]
