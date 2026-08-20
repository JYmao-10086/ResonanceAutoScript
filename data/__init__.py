"""城市-商品数据加载。"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd

from config import CITIES_XLSX


def load_cities(xlsx_path: str = CITIES_XLSX) -> Dict[str, List]:
    """读取城市-商品表，返回 {城市: [商品, ...]}。"""
    df = pd.read_excel(xlsx_path, header=None)
    data_dict: Dict[str, List] = {}
    for _, row in df.iterrows():
        header = row[0]
        values = row[1:].tolist()
        data_dict[header] = values
    return data_dict


def cleaned_merchandises(items: List) -> List:
    """去掉 NaN。"""
    return pd.Series(items).dropna().tolist()
