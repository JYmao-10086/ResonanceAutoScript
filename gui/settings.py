"""设置读写。"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any, Dict

from config import DEFAULT_ADB_EXE, SETTINGS_FILE
from state import state

if TYPE_CHECKING:
    from .app import TradingAssistantApp


def collect_settings(app: "TradingAssistantApp") -> Dict[str, Any]:
    return {
        "adb_path": app.adb_location.get(),
        "start_city": app.start_var.get(),
        "end_city": app.end_var.get(),
        "round_trip_times": app.round_trip_times_var.get(),
        "lollipop": app.lollipop_var.get(),
        "gum": app.gum_var.get(),
        "lighter": app.lighter_var.get(),
        "birch_stone": app.birch_stone_var.get(),
        "fatigue_recovery": app.fatigue_recovery_var.get(),
        "auto_catch": app.auto_catch.get(),
        "use_tow": app.use_tow_var.get(),
        "use_iron_coin": app.use_iron_coin_var.get(),
        "tow_times": app.tow_times_var.get(),
        "merchandise": {
            city: {item: var.get() for item, var in city_vars.items()}
            for city, city_vars in app.merchandise_vars.items()
        },
        "fill_merchandise": {
            city: var.get() for city, var in app.fill_merchandise_vars.items()
        },
        "bargain_times": {city: var.get() for city, var in app.bargain_times_vars.items()},
        "bargain_success": {
            city: var.get() for city, var in app.bargain_success_vars.items()
        },
        "raise_price_times": {
            city: var.get() for city, var in app.raise_price_times_vars.items()
        },
        "raise_price_success": {
            city: var.get() for city, var in app.raise_price_success_vars.items()
        },
        "purchase_book": {city: var.get() for city, var in app.purchase_book_vars.items()},
        "bargain_item": {city: var.get() for city, var in app.bargain_item_vars.items()},
        "raise_item": {city: var.get() for city, var in app.raise_item_vars.items()},
    }


def save_settings(app: "TradingAssistantApp", path: str = SETTINGS_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(collect_settings(app), f, ensure_ascii=False, indent=2)


def apply_settings(app: "TradingAssistantApp", settings: Dict[str, Any]) -> None:
    app.adb_location.set(settings.get("adb_path", ""))
    adb_dir = settings.get("adb_path", "")
    if adb_dir:
        state.adb_path = os.path.join(adb_dir, "adb.exe")
    else:
        state.adb_path = DEFAULT_ADB_EXE

    app.start_var.set(settings.get("start_city", ""))
    app.end_var.set(settings.get("end_city", ""))
    app.round_trip_times_var.set(settings.get("round_trip_times", ""))
    app.lollipop_var.set(settings.get("lollipop", ""))
    app.gum_var.set(settings.get("gum", ""))
    app.lighter_var.set(settings.get("lighter", ""))
    app.birch_stone_var.set(settings.get("birch_stone", ""))
    app.fatigue_recovery_var.set(settings.get("fatigue_recovery", ""))
    app.auto_catch.set(settings.get("auto_catch", False))
    app.use_tow_var.set(settings.get("use_tow", False))
    app.use_iron_coin_var.set(settings.get("use_iron_coin", False))
    app.tow_times_var.set(str(settings.get("tow_times", 0)))

    fill_merchandise = settings.get("fill_merchandise", {}) or {}
    merchandise = settings.get("merchandise", {}) or {}
    for city, city_vars in app.merchandise_vars.items():
        if city in fill_merchandise:
            app.fill_merchandise_vars[city].set(fill_merchandise[city])
        for item, var in city_vars.items():
            var.set(merchandise.get(city, {}).get(item, False))

    for city in app.cities.keys():
        if city in app.bargain_times_vars:
            bargain_times = settings.get("bargain_times", {}) or {}
            if city in bargain_times:
                app.bargain_times_vars[city].set(bargain_times[city])
        if city in app.bargain_success_vars:
            bargain_success = settings.get("bargain_success", {}) or {}
            if city in bargain_success:
                app.bargain_success_vars[city].set(bargain_success[city])
        if city in app.raise_price_times_vars:
            raise_price_times = settings.get("raise_price_times", {}) or {}
            if city in raise_price_times:
                app.raise_price_times_vars[city].set(raise_price_times[city])
        if city in app.raise_price_success_vars:
            raise_price_success = settings.get("raise_price_success", {}) or {}
            if city in raise_price_success:
                app.raise_price_success_vars[city].set(raise_price_success[city])
        if city in app.purchase_book_vars:
            purchase_book = settings.get("purchase_book", {}) or {}
            if city in purchase_book:
                app.purchase_book_vars[city].set(purchase_book[city])
        if city in app.bargain_item_vars:
            bargain_item = settings.get("bargain_item", {}) or {}
            if city in bargain_item:
                app.bargain_item_vars[city].set(bargain_item[city])
        if city in app.raise_item_vars:
            raise_item = settings.get("raise_item", {}) or {}
            if city in raise_item:
                app.raise_item_vars[city].set(raise_item[city])


def load_settings(app: "TradingAssistantApp", path: str = SETTINGS_FILE) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        apply_settings(app, settings)
    except FileNotFoundError:
        state.adb_path = DEFAULT_ADB_EXE
    except (json.JSONDecodeError, KeyError, TypeError):
        # 设置损坏时沿用默认
        state.adb_path = DEFAULT_ADB_EXE
