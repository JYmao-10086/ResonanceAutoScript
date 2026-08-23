"""跑商工作线程。"""

from __future__ import annotations

import math
import re
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union


from adb_ops.client import AdbClient
from config import (
    EXCHANGE_TAP_OFFSET_Y,
    MAP_CITY_COORDS,
    MAP_SWIPE_CENTER_X,
    MAP_SWIPE_CENTER_Y,
    MAP_SWIPE_DURATION,
    MAP_SWIPE_HOLD_DELAY,
    MAP_SWIPE_MAX_HEIGHT,
    MAP_SWIPE_MAX_WIDTH,
    MAP_SWIPE_SETTLE_DELAY,
    picture_path,
    TOW_TIMES_BOX,
)
from state import state
from utils.image import cv_imread
from vision import ocr
from vision.template import match_template
from .base import ControllableThread
from .rubbish import PickUpRubbish

if TYPE_CHECKING:
    from gui.app import TradingAssistantApp


class TradingThread(ControllableThread):
    def __init__(
        self,
        app: "TradingAssistantApp",
        start: str,
        end: str,
        times: Union[str, int],
        lollipop: Union[str, int],
        gum: Union[str, int],
        lighter: Union[str, int],
        birch_stone: Union[str, int],
        fatigue_recovery_var: bool,
    ) -> None:
        super().__init__()
        self.app = app
        self.starte = start
        self.end = end
        self.times = int(times)
        self.lollipop = int(lollipop)
        self.gum = int(gum)
        self.lighter = int(lighter)
        self.birch_stone = int(birch_stone)
        self.fatigue_recovery_var = fatigue_recovery_var
        self.i = 0
        self.client = AdbClient()

    def run(self) -> None:
        self.app.update_log("跑商开始，请返回主界面")
        while self.times > self.i:
            if not self.stopped.is_set():
                if not self.should_continue():
                    self.i = self.times
                    break
                self.app.update_log(f"开始执行第{self.i + 1}趟跑商")
                self.trip(start=self.starte, end=self.end)
                place = self.starte
                self.starte = self.end
                self.end = place
                self.i = self.i + 1
            else:
                self.i = self.times
                self.stop()
                self.join()
        self.app.update_log("跑商结束\n")
        from gui.app import set_enabled

        set_enabled(self.app.stop_trading_button, False)
        set_enabled(self.app.pause_trading_button, False)
        set_enabled(self.app.resume_trading_button, False)
        set_enabled(self.app.round_trip_button, True)
        set_enabled(self.app.one_way_button, True)

    def take_screenshot(self) -> None:
        self.client.take_screenshot()

    def trip(self, start: str, end: str) -> None:
        for _ in range(2):
            if not self.should_continue():
                return
            home = self.find_template("主界面")
            if not home:
                break
            self.check_template(home)
        current_city = self.detect_current_city()
        if current_city not in (start, end):
            self.app.update_log(f"当前城市 {current_city or '未知'} 不在路线中，结束本趟")
            return
        if self.i == 0 and current_city == end:
            self.app.update_log(f"当前位于终点城市{end}，互换起点与终点")
            self.starte, self.end = self.end, self.starte
            start, end = end, start
        self.app.update_log(f"当前位于{current_city}，访问城市")
        self.find_and_check("访问城市")

        merchandises = self.app.merchandise_vars[current_city]
        fill_merchandise = self.app.fill_merchandise_vars[current_city].get()
        no_need_buy = all(val.get() is False for val in merchandises.values()) and fill_merchandise == ""
        if self.app.already_bought_var.get():
            self.app.already_bought_var.set(False)
            no_need_buy = True
        if no_need_buy:
            self.app.update_log("无需要购买商品，返回主界面")
            for _ in range(3):
                if not self.should_continue():
                    return
                home = self.find_template("主界面")
                if not home:
                    break
                self.check_template(home)
        else:
            self.find_and_check(
            current_city + "交易所", old_templste=current_city, tap_offset=(0, EXCHANGE_TAP_OFFSET_Y)
        )
            self.find_and_check("我要买", old_templste=current_city + "交易所")

            if self.should_continue():
                purchase_book_value = int(self.app.purchase_book_vars[current_city].get())
                if purchase_book_value > 0:
                    self.app.update_log(f"使用道具：进货采买书 {purchase_book_value}")
                    while self.should_continue():
                        templste_location = self.find_template("使用道具")
                        if templste_location:
                            self.check_template(templste_location)
                            break
                    while self.should_continue():
                        templste_location = self.find_template("道具/进货采买书")
                        if templste_location:
                            templste_location[0] = templste_location[0] + 280
                            self.check_template(templste_location)
                            break
                    while self.should_continue():
                        templste_location = self.find_template("+1")
                        if templste_location:
                            break
                    for _ in range(purchase_book_value - 1):
                        if not self.should_continue():
                            break
                        self.check_template(templste_location)
                        time.sleep(0.5)
                    while self.should_continue():
                        templste_location = self.find_template("确认")
                        if templste_location:
                            self.check_template(templste_location)
                            break

            if self.should_continue():
                self.buy_merchandise(merchandises, fill_merchandise)

            if self.should_continue():
                bargain_times = int(self.app.bargain_times_vars[current_city].get())
                bargain_success = int(self.app.bargain_success_vars[current_city].get())
                if bargain_times > 0:
                    self.bargain(
                        "砍价",
                        bargain_times,
                        bargain_success,
                        item_name=self.app.bargain_item_vars[current_city].get() or None,
                    )
                    self.app.update_log("砍价完成")

            while self.should_continue():
                templste_location = self.find_template("触碰空白区域退出", threshold=0.99)
                if templste_location:
                    self.check_template(templste_location)
                    break
                self.find_and_check("买入", times=1)

            self.find_and_check("主界面", old_templste="触碰空白区域退出", threshold=0.99)
        self.find_and_check("启程", old_templste="主界面")

        if self.should_continue():
            templste_location = self.find_map_place(end, current_city=current_city)
            if templste_location:
                self.check_template(templste_location)
                self.app.update_log(f"终点站：{end}")

        tow_used = False
        if self.app.use_tow_var.get():
            tow_times = int(self.app.tow_times_var.get() or 0)
            if tow_times <= 0:
                self.app.update_log("拖车次数为 0，不使用拖车")
            else:
                tow_used = self.use_tow_service()
                if tow_used:
                    self.app.tow_times_var.set(str(tow_times - 1))
        if not tow_used:
            self.find_and_check("前往目的地", "地图/" + end)

        if self.app.auto_catch.get():
            catch_rubbish = PickUpRubbish()
            state.catch_rubbish = catch_rubbish
            catch_rubbish.start()

        self.find_and_check("进入站点")

        if self.app.auto_catch.get() and state.catch_rubbish is not None:
            state.catch_rubbish.stop()

        self.find_and_check("访问城市", old_templste="进入站点")
        self.find_and_check(
            end + "交易所", end, tap_offset=(0, EXCHANGE_TAP_OFFSET_Y)
        )
        self.find_and_check("我要卖", end + "交易所")
        self.find_and_check("全部卖出", old_templste="我要卖", times=1.5)

        if self.should_continue():
            templste_location = self.find_template("空货仓")
            if not templste_location:
                if self.should_continue():
                    raise_price_times = int(self.app.raise_price_times_vars[start].get())
                    raise_price_success = int(self.app.raise_price_success_vars[start].get())
                    if raise_price_times > 0:
                        self.bargain(
                            "抬价",
                            raise_price_times,
                            raise_price_success,
                            item_name=self.app.raise_item_vars[start].get() or None,
                        )
                        self.app.update_log("抬价完成")

                while self.should_continue():
                    templste_location = self.find_template("触碰空白区域退出", threshold=0.99)
                    if templste_location:
                        self.check_template(templste_location)
                        break
                    self.find_and_check("卖出", times=1)
            else:
                self.app.update_log("无可售卖物品，将返回主界面")

        self.find_and_check("主界面", "触碰空白区域退出")

    def find_and_check(
        self,
        templste: str,
        old_templste: str = "",
        times: float = 0.1,
        threshold: float = 0.9,
        tap_offset=(0, 0),
    ) -> None:
        while self.should_continue():
            templste_location = self.find_template(templste, threshold)
            if templste_location:
                self.check_template(
                    [
                        templste_location[0] + tap_offset[0],
                        templste_location[1] + tap_offset[1],
                    ]
                )
                self.app.update_log(templste)
                time.sleep(times)
                break
            if old_templste != "":
                old_templste_location = self.find_template(old_templste)
                if old_templste_location:
                    self.check_template(old_templste_location)
                    time.sleep(times)

    def find_map_place(self, place: str, current_city: Optional[str] = None) -> Optional[List[int]]:
        target = MAP_CITY_COORDS.get(place)
        for _ in range(2):
            if not self.should_continue():
                break
            place_location = self.find_template(f"地图/{place}", threshold=0.8)
            if place_location:
                return place_location

        if target is None:
            self.app.update_log(f"缺少 {place} 的地图坐标，无法滑动")
            return None
        current = MAP_CITY_COORDS.get(current_city or self.starte)
        if current is None:
            self.app.update_log("无法识别当前城市，无法滑动地图")
            return None
        self.app.update_log(f"未找到{place}，滑动地图")
        offset = [current[0] - target[0], current[1] - target[1]]
        steps = max(
            1,
            math.ceil(abs(offset[0]) / MAP_SWIPE_MAX_WIDTH),
            math.ceil(abs(offset[1]) / MAP_SWIPE_MAX_HEIGHT),
        )
        for _ in range(steps):
            if not self.should_continue():
                return None
            self.adb_map_swipe(offset[0] / steps, offset[1] / steps)
        for _ in range(2):
            if not self.should_continue():
                break
            place_location = self.find_template(f"地图/{place}", threshold=0.8)
            if place_location:
                return place_location
        return None

    def detect_current_city(self) -> Optional[str]:
        self.take_screenshot()
        items = ocr.ocr_image_path(picture_path("screenshot.png"))
        for city in MAP_CITY_COORDS:
            if ocr.find_text(items, city) is not None:
                return city
        return None

    def physical_power(self) -> bool:
        if not self.should_continue():
            return False

        if self.lollipop > 0 and self.should_continue():
            templste_location = self.find_template("提神棒棒糖")
            if templste_location:
                templste_location[1] = templste_location[1] - 150
                self.check_template(templste_location, 1)
                self.find_and_check("补充")
                self.lollipop = self.lollipop - 1
                self.app.update_log(f"使用提神棒棒糖，还剩{self.lollipop}")
                return True

        if self.gum > 0 and self.should_continue():
            templste_location = self.find_template("提神口香糖")
            if templste_location:
                templste_location[1] = templste_location[1] - 150
                self.check_template(templste_location, 1)
                self.find_and_check("补充")
                self.gum = self.gum - 1
                self.app.update_log(f"使用提神口香糖，还剩{self.gum}")
                return True

        if self.lighter > 0 and self.should_continue():
            templste_location = self.find_template("仙人掌提神跳糖")
            if templste_location:
                templste_location[1] = templste_location[1] - 150
                self.check_template(templste_location, 1)
                self.find_and_check("补充")
                self.lighter = self.lighter - 1
                self.app.update_log(f"使用仙人掌提神跳糖，还剩{self.lighter}")
                return True

        if self.birch_stone > 0 and self.should_continue():
            templste_location = self.find_template("疲劳桦石")
            if templste_location:
                templste_location[1] = templste_location[1] - 150
                self.check_template(templste_location, 1)
                self.find_and_check("补充")
                self.birch_stone = self.birch_stone - 1
                self.app.update_log(f"使用桦石，还剩{self.birch_stone}")
                return True

        return False

    def use_item(self, item_name: str) -> None:
        while self.should_continue():
            loc = self.find_template("使用道具")
            if loc:
                self.check_template(loc)
                break
        while self.should_continue():
            loc = self.find_template(f"道具/{item_name}")
            if loc:
                loc[0] = loc[0] + 280
                self.check_template(loc)
                break

    def use_tow_service(self) -> bool:
        for _ in range(2):
            loc = self.find_template("拖车服务")
            if loc:
                self.check_template(loc)
                break
        else:
            return False
        time.sleep(1)
        self.take_screenshot()
        image = cv_imread(picture_path("screenshot.png"))
        x1, y1, x2, y2 = TOW_TIMES_BOX
        items = ocr.ocr_image(image)
        count = None
        for item in items:
            cx, cy = item["center"]
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                match = re.search(r"(\d+)", "".join(item["text"].split()))
                if match:
                    count = int(match.group(1))
                    break
        if count is None or count <= 0:
            self.app.update_log("拖车次数不足，按正常方式前往")
            self.find_and_check("取消")
            return False
        if not self.app.use_iron_coin_var.get():
            self.find_and_check("拖车/里程点数")
        self.find_and_check("确认")
        return True

    def bargain(self, bargain: str, bargain_times: int, bargain_success: int, item_name: Optional[str] = None) -> None:
        if item_name:
            self.use_item(item_name)
        success = 0
        times = 0
        prev_range: Optional[float] = None
        while success < bargain_success and times < bargain_times and self.should_continue():
            if not self.should_continue():
                break
            bargain_location = self.find_template(bargain)
            if not bargain_location:
                continue
            if not self.should_continue():
                return
            if prev_range is None:
                prev_range = self._read_bargain_range(bargain)
            if prev_range is not None and prev_range >= 20:
                break
            self.check_template(bargain_location, times=2)
            if self.fatigue_recovery_var:
                if self.lollipop > 0 or self.gum > 0 or self.lighter > 0 or self.birch_stone > 0:
                    flag = self.physical_power()
                    if flag:
                        continue
            new_range = self._read_bargain_range(bargain)
            if new_range is not None and prev_range is not None and new_range != prev_range:
                self.app.update_log("交涉成功")
                success = success + 1
            else:
                self.app.update_log("交涉失败")
            prev_range = new_range
            times = times + 1
            self.app.update_log(f"{bargain}{times}次，成功{success}次")

    def _read_bargain_range(self, bargain: str) -> Optional[float]:
        self.take_screenshot()
        items = ocr.ocr_image_path(picture_path("screenshot.png"))
        anchor = None
        for item in items:
            text = "".join(item["text"].split())
            if f"{bargain}幅度" in text or "幅度" in text:
                anchor = item
                break
        if anchor is None:
            return None

        def _extract(text: str) -> Optional[float]:
            match = re.search(r"(\d+(?:\.\d+)?)\s*%", "".join(text.split()))
            return float(match.group(1)) if match else None

        value = _extract(anchor["text"])
        if value is not None:
            return value
        for item in items:
            if abs(item["center"][1] - anchor["center"][1]) <= 40:
                value = _extract(item["text"])
                if value is not None:
                    return value
        return None

    def buy_merchandise(self, merchandises: Any, fill_merchandise: str = "") -> None:
        need_merchandises: List[str] = []
        bought_merchandises: List[str] = []
        filp = True
        i = 0
        if isinstance(merchandises, str):
            need_merchandises.append(merchandises)
            filp = False
        else:
            for merchandise, state_var in merchandises.items():
                if state_var.get():
                    need_merchandises.append(merchandise)
            if fill_merchandise:
                need_merchandises.append(fill_merchandise)
            if need_merchandises and not fill_merchandise and all(state_var.get() for state_var in merchandises.values()):
                self.app.update_log("已选全部商品，直接全部买入")
                self.find_and_check("全部买入")
                return

        while self.should_continue():
            self.take_screenshot()
            for merchandise in need_merchandises:
                if merchandise not in bought_merchandises:
                    location = self.find_template("商品/" + merchandise, threshold=0.95)
                    if location:
                        self.check_template(location)
                        self.app.update_log(f"添加{merchandise}")
                        bought_merchandises.append(merchandise)
                        continue

            self.app.update_log("滑动商品栏")
            if filp:
                self.adb_input_swipe(1020, 1000, 1020, 250)
                i = i + 1
                if i % 3 == 2:
                    filp = False
            else:
                self.adb_input_swipe(1020, 250, 1020, 1000)
                i = i + 1
                if i % 3 == 2:
                    filp = True
            if set(bought_merchandises) == set(need_merchandises):
                break

    def find_template(
        self,
        name: str,
        threshold: float = 0.9,
        take_screenshot: bool = True,
        base: str = "screenshot",
        cut: Optional[List[int]] = None,
    ) -> Union[List[int], bool]:
        if not self.should_continue():
            return False
        if take_screenshot:
            self.take_screenshot()
        return match_template(name, threshold=threshold, base=base, cut=cut)

    def check_template(self, template_center_location, times: float = 0.5) -> None:
        if not self.should_continue():
            return
        self.client.tap(
            template_center_location[0],
            template_center_location[1],
            delay=times,
        )

    def adb_swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 500,
        times: float = 1,
    ) -> None:
        if not self.should_continue():
            return
        self.client.swipe(start_x, start_y, end_x, end_y, duration=duration, delay=times)

    def adb_input_swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        times: float = 1,
    ) -> None:
        if not self.should_continue():
            return
        self.client.drag_and_drop(start_x, start_y, end_x, end_y, delay=times)


    def adb_map_swipe(self, dx: float, dy: float) -> None:
        if not self.should_continue():
            return
        self.client.swipe_with_hold(
            MAP_SWIPE_CENTER_X,
            MAP_SWIPE_CENTER_Y,
            MAP_SWIPE_CENTER_X + int(round(dx)),
            MAP_SWIPE_CENTER_Y + int(round(dy)),
            duration=MAP_SWIPE_DURATION,
            hold_delay=MAP_SWIPE_HOLD_DELAY,
            delay=MAP_SWIPE_SETTLE_DELAY,
        )

    def stop_when_finished(self) -> None:
        self.i = self.times
