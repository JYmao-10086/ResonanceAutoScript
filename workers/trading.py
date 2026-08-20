"""跑商工作线程。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import cv2

from adb_ops.client import AdbClient
from config import MAP_IMAGE_PATH, picture_path
from state import state
from utils.image import cv_imread
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
        while not self.stopped.is_set():
            if not self.should_continue():
                break
            templste_location = self.find_template(start)
            if templste_location:
                self.check_template(templste_location)
                self.app.update_log(f"当前位于{start}")
                break
            templste_location = self.find_template("主界面")
            if templste_location:
                self.check_template(templste_location)
                self.app.update_log("返回主界面")

        merchandises = self.app.merchandise_vars[start]
        fill_merchandise = self.app.fill_merchandise_vars[start].get()
        if all(val.get() is False for val in merchandises.values()) and fill_merchandise == "":
            self.app.update_log("无需要购买商品，返回主界面")
        else:
            self.find_and_check(start + "交易所", old_templste=start)
            self.find_and_check("我要买", old_templste=start + "交易所")

            if self.should_continue():
                purchase_book_value = int(self.app.purchase_book_vars[start].get())
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
                self.buy_merchandise(merchandises)

            if self.should_continue() and fill_merchandise != "":
                self.buy_merchandise(fill_merchandise)

            if self.should_continue():
                bargain_times = int(self.app.bargain_times_vars[start].get())
                bargain_success = int(self.app.bargain_success_vars[start].get())
                if bargain_times > 0:
                    self.bargain("砍价", bargain_times, bargain_success)
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
            templste_location = self.find_map_place(end)
            if templste_location:
                self.check_template(templste_location)
                self.app.update_log(f"终点站：{end}")

        self.find_and_check("前往目的地", "地图/" + end)

        if self.app.auto_catch.get():
            catch_rubbish = PickUpRubbish()
            state.catch_rubbish = catch_rubbish
            catch_rubbish.start()

        self.find_and_check("进入站点")

        if self.app.auto_catch.get() and state.catch_rubbish is not None:
            state.catch_rubbish.stop()

        self.find_and_check(end, "进入站点")
        self.find_and_check(end + "交易所", end)
        self.find_and_check("我要卖", end + "交易所")
        self.find_and_check("全部卖出", old_templste="我要卖", times=1.5)

        if self.should_continue():
            templste_location = self.find_template("空货仓")
            if not templste_location:
                if self.should_continue():
                    raise_price_times = int(self.app.raise_price_times_vars[end].get())
                    raise_price_success = int(self.app.raise_price_success_vars[end].get())
                    if raise_price_times > 0:
                        self.bargain("抬价", raise_price_times, raise_price_success)
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
    ) -> None:
        while self.should_continue():
            templste_location = self.find_template(templste, threshold)
            if templste_location:
                self.check_template(templste_location)
                self.app.update_log(templste)
                time.sleep(times)
                break
            if old_templste != "":
                old_templste_location = self.find_template(old_templste)
                if old_templste_location:
                    self.check_template(old_templste_location)
                    time.sleep(times)

    def find_map_place(self, place: str) -> Optional[List[int]]:
        while self.should_continue():
            for _ in range(2):
                if not self.should_continue():
                    break
                place_location = self.find_template(f"地图/{place}", threshold=0.8)
                if place_location:
                    return place_location

            self.app.update_log(f"未找到{place}，滑动地图")
            cv2.imread(MAP_IMAGE_PATH)
            end_location = self.find_template("地图/" + place, threshold=0.1, base="map")
            my_location = self.find_template("screenshot", threshold=0.1, base="map", cut=[180, 120])
            while my_location is False:
                if self.should_continue():
                    my_location = self.find_template(
                        "screenshot", threshold=0.1, base="map", cut=[180, 120]
                    )
                    print(my_location)
                else:
                    return None
            my_location = [my_location[0] - 90, my_location[1] - 60]
            coordinate_vector = [
                my_location[0] - end_location[0],
                my_location[1] - end_location[1],
            ]
            for _ in range(3):
                self.adb_swipe(
                    960,
                    540,
                    960 + coordinate_vector[0] // 3,
                    540 + coordinate_vector[1] // 3,
                    times=0.2,
                )
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

    def bargain(self, bargain: str, bargain_times: int, bargain_success: int) -> None:
        def contrast_bargain_range(new_bargain, old_bargain):
            result = cv2.matchTemplate(new_bargain, old_bargain, cv2.TM_CCOEFF_NORMED)
            theight, twidth = old_bargain.shape[:2]
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            x = max_loc[0]
            y = max_loc[1]
            new_bargain = new_bargain[y : y + theight, x : x + twidth]
            result = cv2.matchTemplate(new_bargain, old_bargain, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            print(f"对比结果:{max_val}")
            if max_val > 0.99:
                return False, old_bargain
            return True, new_bargain

        success = 0
        times = 0
        max_bargain_range = False
        old_bargain = cv_imread(picture_path(f"{bargain}幅度0%.png"))

        while success < bargain_success and times < bargain_times and not max_bargain_range:
            if not self.should_continue():
                break
            bargain_location = self.find_template(bargain)
            if bargain_location:
                if not self.should_continue():
                    return
                self.check_template(bargain_location, times=2)
                if self.fatigue_recovery_var:
                    if self.lollipop > 0 or self.gum > 0 or self.lighter > 0 or self.birch_stone > 0:
                        flag = self.physical_power()
                        if flag:
                            continue
                bargain_result = False
                while self.should_continue():
                    bargain_location = self.find_template(bargain)
                    if bargain_location:
                        new_bargain = cv2.imread(picture_path("screenshot.png"))
                        bargain_result, old_bargain = contrast_bargain_range(
                            new_bargain, old_bargain
                        )
                        break
                if bargain_result:
                    self.app.update_log("交涉成功")
                    success = success + 1
                else:
                    self.app.update_log("交涉失败")
                times = times + 1
                self.app.update_log(f"{bargain}{times}次，成功{success}次")
                max_bargain_range = self.find_template("砍价幅度20%", 0.99)

    def buy_merchandise(self, merchandises: Any) -> None:
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

    def stop_when_finished(self) -> None:
        self.i = self.times
