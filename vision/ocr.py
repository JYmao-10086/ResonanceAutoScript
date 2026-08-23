"""PP-OCRv5 中文 OCR 封装（RapidOCR + 项目 models 目录）。"""

from __future__ import annotations

import os
import threading
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from config import OCR_DET_MODEL, OCR_KEYS_PATH, OCR_REC_MODEL, OCR_TEXT_SCORE
from utils.image import cv_imread

_engines: Dict[bool, Any] = {}
_engine_lock = threading.Lock()
_cache: Dict[Tuple[str, float, int, bool], List[Dict[str, Any]]] = {}
_CACHE_MAX = 32


def _get_engine(high_res: bool = False) -> Any:
    """懒加载 RapidOCR 引擎（带线程锁）。

    普通截图用默认检测分辨率；大地图（如 picture/map.png 这类大尺寸底图）
    用高分辨率检测，否则城市名等小字会被过度压缩导致识别错字。
    """
    global _engines
    engine = _engines.get(high_res)
    if engine is None:
        with _engine_lock:
            engine = _engines.get(high_res)
            if engine is None:
                from rapidocr import RapidOCR
                from rapidocr.utils.typings import ModelType, OCRVersion

                params: Dict[str, Any] = {
                    "Global.use_cls": False,
                    "Global.log_level": "error",
                    "Det.model_path": OCR_DET_MODEL,
                    "Det.model_type": ModelType.MOBILE,
                    "Det.ocr_version": OCRVersion.PPOCRV5,
                    "Rec.model_path": OCR_REC_MODEL,
                    "Rec.model_type": ModelType.MOBILE,
                    "Rec.ocr_version": OCRVersion.PPOCRV5,
                    "Rec.rec_keys_path": OCR_KEYS_PATH,
                }
                if high_res:
                    # 大尺寸底图：限制最大边并提高检测最小边，保留小字细节
                    params["Global.max_side_len"] = 6000
                    params["Det.limit_side_len"] = 2000
                    params["Det.limit_type"] = "min"
                engine = RapidOCR(params=params)
                _engines[high_res] = engine
    return engine


def _parse_result(result: Any) -> List[Dict[str, Any]]:
    """把 RapidOCR 结果转成 [{text, score, box, center}, ...]。"""
    items: List[Dict[str, Any]] = []
    txts = getattr(result, "txts", None)
    scores = getattr(result, "scores", None)
    boxes = getattr(result, "boxes", None)
    if txts is None or scores is None or boxes is None:
        return items
    for text, score, box in zip(txts, scores, boxes):
        box = np.asarray(box, dtype=float)
        center = box.mean(axis=0).round().astype(int).tolist()
        items.append({"text": text, "score": float(score), "box": box, "center": center})
    return items


def ocr_image(image: np.ndarray, high_res: bool = False) -> List[Dict[str, Any]]:
    """识别图像 ndarray 中的文字。"""
    result = _get_engine(high_res)(image)
    return _parse_result(result)


def ocr_image_path(path: str, high_res: bool = False) -> List[Dict[str, Any]]:
    """识别图片文件中的文字；同一文件未变化时复用缓存结果。"""
    key = None
    try:
        key = (path, os.path.getmtime(path), os.path.getsize(path), high_res)
    except OSError:
        key = None
    if key is not None and key in _cache:
        return _cache[key]
    image = cv_imread(path)
    if image is None:
        return []
    items = ocr_image(image, high_res=high_res)
    if key is not None:
        if len(_cache) >= _CACHE_MAX:
            _cache.clear()
        _cache[key] = items
    return items


def find_text(
    items: List[Dict[str, Any]],
    target: str,
    min_score: float = OCR_TEXT_SCORE,
    contains: bool = False,
) -> Optional[List[int]]:
    """在 OCR 结果中查找目标文字，返回中心点 [x, y] 或 None。"""
    for item in items:
        if item["score"] < min_score:
            continue
        text = "".join(item["text"].split()).strip("“”\"'「」")
        if contains:
            if target in text:
                return item["center"]
        elif text == target:
            return item["center"]
    return None
