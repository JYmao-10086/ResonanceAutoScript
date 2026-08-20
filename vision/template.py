"""模板匹配。"""

from __future__ import annotations

from typing import List, Optional, Union

import cv2

from config import picture_path
from utils.image import cv_imread


def match_template(
    name: str,
    threshold: float = 0.9,
    base: str = "screenshot",
    cut: Optional[List[int]] = None,
) -> Union[List[int], bool]:
    """
    在 base 图中匹配 picture/{name}.png。
    成功返回中心点 [x, y]，失败返回 False。
    """
    if cut is None:
        cut = [0, 0]

    image = cv_imread(picture_path(f"{base}.png"))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    template = cv_imread(picture_path(f"{name}.png"))
    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    theight, twidth = template.shape[:2]
    template = template[cut[1] : theight - cut[1], cut[0] : twidth - cut[0]]
    theight, twidth = template.shape[:2]

    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    print(f"开始匹配：{name}")
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print(f"{max_val}:{max_loc}")
    print(f"{twidth}:{theight}")

    if max_val > threshold:
        center_x = twidth // 2 + max_loc[0]
        center_y = theight // 2 + max_loc[1]
        print(center_x, " ", center_y)
        return [center_x, center_y]
    return False
