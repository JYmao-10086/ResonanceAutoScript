from collections.abc import Callable, Iterable, Mapping
import tkinter as tk
from tkinter import ttk
import json
from typing import Any
import numpy as np
import pandas as pd
import subprocess
import time
import os
import threading
import cv2

global trading_thread
global catch_rubbish
global port
port = '7555'
# global auto_tree
# current_dir = os.path.dirname(os.path.abspath(__file__))
# pytesseract.pytesseract.tesseract_cmd = current_dir+r'\Tesseract-OCR\tesseract'
# 构建adb的完整路径
# adb_path = os.path.join('D:\Program Files\YXResonanceSolstice-12.0\shell', 'adb.exe')

def cv_imread(file_path):
    cv_img = cv2. imdecode(np.fromfile(file_path, dtype=np.uint8),-1)
    return cv_img

# class AutoTree(threading.Thread):
#     def __init__(self, cactus_pop, cactus_jump, cactus_energy, birch_stone):
#         super().__init__()
#         self.cactus_pop = int(cactus_pop)
#         self.cactus_jump = int(cactus_jump)
#         self.cactus_energy = int(cactus_energy)
#         self.birch_stone = int(birch_stone)
#         self.stopped = threading.Event()
#         self.paused = threading.Event()
#         self.paused.set()

#     def run(self):
class PickUpRubbish(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stopped = threading.Event()
        self.paused = threading.Event()
        self.paused.set()

    def run(self):
        while not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            self.pick_up_rubbish()

    def pick_up_rubbish(self):
        if not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            subprocess.run([adb_path, "shell", "input", "tap", "1151", "725"], creationflags=0x08000000)
            time.sleep(0.1)
    def stop(self):
        self.stopped.set()

    def pause(self):
        self.paused.clear()

    def resume(self):
        self.paused.set()


class TradingThread(threading.Thread):
    def __init__(self, start, end, times, lollipop, gum, lighter, birch_stone, fatigue_recovery_var):
        super().__init__()
        self.starte = start
        self.end = end
        self.times = int(times)
        self.lollipop = int(lollipop)
        self.gum = int(gum)
        self.lighter = int(lighter)
        self.birch_stone = int(birch_stone)
        self.fatigue_recovery_var = fatigue_recovery_var
        self.stopped = threading.Event()
        self.paused = threading.Event()
        self.paused.set()
        self.i = 0

    def run(self):
        app.update_log("跑商开始，请返回主界面")
        while self.times > self.i:
            if not self.stopped.is_set():
                while not self.paused.is_set():
                    self.paused.wait()
                    if self.stopped.is_set():
                        self.i = self.times
                        break
                # 执行往返跑商操作
                app.update_log(f"开始执行第{self.i+1}趟跑商")
                self.trip(start=self.starte, end=self.end)
                place = self.starte
                self.starte = self.end
                self.end = place
                self.i=self.i+1
            else:
                self.i = self.times
                self.stop()
                self.join()
        app.update_log("跑商结束\n")
        app.stop_trading_button.config(state=tk.DISABLED)
        app.pause_trading_button.config(state=tk.DISABLED)
        app.resume_trading_button.config(state=tk.DISABLED)
        app.round_trip_button.config(state=tk.NORMAL)
        app.one_way_button.config(state=tk.NORMAL)


    def take_screenshot(self):
        # 使用ADB命令截取MuMu模拟器截图
        global port
        subprocess.run([adb_path, '-s', f'127.0.0.1:{port}', "shell", "screencap", "/sdcard/screenshot.png"], creationflags=0x08000000)
        print("已截图")
        # 从设备中拉取截图文件到本地
        subprocess.run([adb_path, '-s', f'127.0.0.1:{port}', "pull", "/sdcard/screenshot.png", "picture/screenshot.png"], creationflags=0x08000000)
        print("已保存至本地")


    def trip(self, start, end):
        while not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            #检测是否在起点
            templste_location = self.find_template(start)
            if templste_location:
                self.check_template(templste_location)
                app.update_log(f"当前位于{start}")
                break
            else:
                templste_location = self.find_template("主界面")
                if templste_location:
                    self.check_template(templste_location)
                    app.update_log("返回主界面")

        merchandises = app.merchandise_vars[start]#起点城市商品变量
        fill_merchandise = app.fill_merchandise_vars[start].get()  #填补商品变量
        if all(val.get() == False for val in merchandises.values()) and fill_merchandise == '':
            app.update_log("无需要购买商品，返回主界面")
        else:
            
            self.find_and_check(start+"交易所", old_templste=start)

            self.find_and_check("我要买", old_templste=start+"交易所")

            if not self.stopped.is_set():
                while not self.paused.is_set():
                    self.paused.wait()
                    if self.stopped.is_set():
                        break
                #使用进货采买书
                purchase_book_value = int(app.purchase_book_vars[start].get())
                if purchase_book_value > 0:
                    app.update_log(f"使用道具：进货采买书 {purchase_book_value}")
                    while not self.stopped.is_set():
                        while not self.paused.is_set():
                            self.paused.wait()
                            if self.stopped.is_set():
                                break
                        templste_location = self.find_template('使用道具')
                        if templste_location:
                            self.check_template(templste_location)
                            break
                    while not self.stopped.is_set():
                        while not self.paused.is_set():
                            self.paused.wait()
                            if self.stopped.is_set():
                                break
                        templste_location = self.find_template('道具/进货采买书')#280
                        if templste_location:
                            templste_location[0] = templste_location[0]+280
                            self.check_template(templste_location)
                            break
                    while not self.stopped.is_set():
                        while not self.paused.is_set():
                            self.paused.wait()
                            if self.stopped.is_set():
                                break
                        templste_location = self.find_template('+1')
                        if templste_location:
                            break
                    for i in range(purchase_book_value-1):
                        if not self.stopped.is_set():
                            while not self.paused.is_set():
                                self.paused.wait()
                                if self.stopped.is_set():
                                    break
                            self.check_template(templste_location)
                            time.sleep(0.5)
                    while not self.stopped.is_set():
                        while not self.paused.is_set():
                            self.paused.wait()
                            if self.stopped.is_set():
                                break
                        templste_location = self.find_template('确认')
                        if templste_location:
                            self.check_template(templste_location)
                            break

            if not self.stopped.is_set():
                while not self.paused.is_set():
                    self.paused.wait()
                    if self.stopped.is_set():
                        break
            # 购买商品
                # merchandises = app.merchandise_vars[start]#起点城市商品变量
                
            if not self.stopped.is_set():
                while not self.paused.is_set():
                    self.paused.wait()
                    if self.stopped.is_set():
                        break
                self.buy_merchandise(merchandises)
            
            if not self.stopped.is_set():
                while not self.paused.is_set():
                    self.paused.wait()
                    if self.stopped.is_set():
                        break
                #填补商品
                # fill_merchandise = app.fill_merchandise_vars[start].get()  #填补商品变量
                if fill_merchandise != '':
                    self.buy_merchandise(fill_merchandise)

            if not self.stopped.is_set():
                while not self.paused.is_set():
                    self.paused.wait()
                    if self.stopped.is_set():
                        break
                #开始砍价
                bargain_times = int(app.bargain_times_vars[start].get())  # 砍价次数变量
                bargain_success = int(app.bargain_success_vars[start].get())  # 砍价成功次数变量
                if bargain_times > 0:
                    self.bargain('砍价', bargain_times, bargain_success)
                    app.update_log('砍价完成')
            
            while not self.stopped.is_set():
                while not self.paused.is_set():
                    self.paused.wait()
                    if self.stopped.is_set():
                        break
                templste_location = self.find_template("触碰空白区域退出", threshold=0.99)
                if templste_location:
                    self.check_template(templste_location)
                    break
                else:
                    self.find_and_check("买入", times=1)
        

        self.find_and_check("主界面", old_templste="触碰空白区域退出", threshold=0.99)

        self.find_and_check("启程", old_templste="主界面")

        if not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            #选择终点站
            templste_location = self.find_map_place(end)
            self.check_template(templste_location)
            app.update_log(f"终点站：{end}")
            
        self.find_and_check("前往目的地", "地图/"+end)

        if app.auto_catch.get():
            global catch_rubbish
            catch_rubbish = PickUpRubbish()
            catch_rubbish.start()

        self.find_and_check("进入站点")

        if app.auto_catch.get():
            catch_rubbish.stop()

        self.find_and_check(end, "进入站点")

        self.find_and_check(end+"交易所", end)

        self.find_and_check("我要卖", end+"交易所")

        self.find_and_check("全部卖出", old_templste="我要卖", times=1.5)

        if not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            templste_location = self.find_template("空货仓")
            if not templste_location:

                if not self.stopped.is_set():
                    while not self.paused.is_set():
                        self.paused.wait()
                        if self.stopped.is_set():
                            break
                    #开始抬价
                    raise_price_times = int(app.raise_price_times_vars[end].get())  # 抬价次数变量
                    raise_price_success = int(app.raise_price_success_vars[end].get())  # 抬价成功次数变量
                    if raise_price_times > 0:
                        self.bargain('抬价', raise_price_times, raise_price_success)
                        app.update_log('抬价完成')
                
                while not self.stopped.is_set():
                    while not self.paused.is_set():
                        self.paused.wait()
                        if self.stopped.is_set():
                            break
                    templste_location = self.find_template("触碰空白区域退出", threshold=0.99)
                    if templste_location:
                        self.check_template(templste_location)
                        break
                    else:
                        self.find_and_check("卖出", times=1)
            else:
                app.update_log("无可售卖物品，将返回主界面")

        self.find_and_check("主界面", "触碰空白区域退出")

    def find_and_check(self, templste, old_templste='', times=0.1, threshold=0.9):
        while not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            templste_location = self.find_template(templste, threshold)
            if templste_location:
                self.check_template(templste_location)
                app.update_log(templste)
                time.sleep(times)
                break
            elif old_templste != '':
                old_templste_location = self.find_template(old_templste)
                if old_templste_location:
                    self.check_template(old_templste_location)
                    time.sleep(times)


    def find_map_place(self, place):
        # filp=0
        while not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            for i in range(2):
                if not self.stopped.is_set():
                    while not self.paused.is_set():
                        self.paused.wait()
                        if self.stopped.is_set():
                            break
                    place_location = self.find_template(f"地图/{place}", threshold=0.8)
                    if place_location:
                        return place_location
                    else:
                        continue
            app.update_log(f"未找到{place}，滑动地图")
            map = cv2.imread("picture/map.png")
            end_location = self.find_template('地图/'+place, threshold=0.1, base="map")
            my_location = self.find_template("screenshot", threshold=0.1, base="map", cut=[180, 120])
            while my_location == False:
                if not self.stopped.is_set():
                    while not self.paused.is_set():
                        self.paused.wait()
                        if self.stopped.is_set():
                            return
                    my_location = self.find_template("screenshot", threshold=0.1, base="map", cut=[180, 120])
                    print(my_location)
                else:
                    return
            my_location = [my_location[0]-90, my_location[1]-60]
            coordinate_vector = [my_location[0]-end_location[0], my_location[1]-end_location[1]]
            for i in range(3):
                self.adb_swipe(960, 540, 960+coordinate_vector[0]//3, 540+coordinate_vector[1]//3, times=0.2)
            # time.sleep(0.5)
            # if filp%6 == 0:
            #     self.adb_swipe(1919, 550, 1, 550)
            #     filp = filp+1
            # elif filp%6 == 1:
            #     self.adb_swipe(960, 1070, 960, 10)
            #     filp = filp+1
            # elif filp%6 == 2:
            #     self.adb_swipe(960, 1070, 960, 10)
                
            #     filp = filp+1
            # elif filp%6 == 3:
            #     self.adb_swipe(1, 550, 1919, 550)
                
            #     filp = filp+1
            # elif filp%6 == 4:
            #     self.adb_swipe(960, 10, 960, 1070)
            #     filp = filp+1
            # elif filp%6 == 5:
            #     self.adb_swipe(960, 10, 960, 1070)
            #     filp = filp+1

    def physical_power(self):
        if not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            if self.lollipop > 0:
                if not self.stopped.is_set():
                    while not self.paused.is_set():
                        self.paused.wait()
                        if self.stopped.is_set():
                            break
                    templste_location = self.find_template("提神棒棒糖")
                    if templste_location:
                        templste_location[1] = templste_location[1]-150
                        self.check_template(templste_location, 1)
                        self.find_and_check("补充")
                        self.lollipop=self.lollipop-1
                        app.update_log(f"使用提神棒棒糖，还剩{self.lollipop}")
                        return True
            if self.gum > 0:
                if not self.stopped.is_set():
                    while not self.paused.is_set():
                        self.paused.wait()
                        if self.stopped.is_set():
                            break
                    templste_location = self.find_template("提神口香糖")
                    if templste_location:
                        templste_location[1] = templste_location[1]-150
                        self.check_template(templste_location, 1)
                        self.find_and_check("补充")
                        self.gum=self.gum-1
                        app.update_log(f"使用提神口香糖，还剩{self.gum}")
                        return True
            if self.lighter > 0:
                if not self.stopped.is_set():
                    while not self.paused.is_set():
                        self.paused.wait()
                        if self.stopped.is_set():
                            break
                    templste_location = self.find_template("仙人掌提神跳糖")
                    if templste_location:
                        templste_location[1] = templste_location[1]-150
                        self.check_template(templste_location, 1)
                        self.find_and_check("补充")
                        self.lighter=self.lighter-1
                        app.update_log(f"使用仙人掌提神跳糖，还剩{self.lighter}")
                        return True
            if self.birch_stone > 0:
                if not self.stopped.is_set():
                    while not self.paused.is_set():
                        self.paused.wait()
                        if self.stopped.is_set():
                            break
                    templste_location = self.find_template("疲劳桦石")
                    if templste_location:
                        templste_location[1] = templste_location[1]-150
                        self.check_template(templste_location, 1)
                        self.find_and_check("补充")
                        self.birch_stone=self.birch_stone-1
                        app.update_log(f"使用桦石，还剩{self.birch_stone}")
                        return True
            return False

    def bargain(self, bargain, bargain_times, bargain_success):
        def contrast_bargain_range(new_bargain, old_bargain):
            result = cv2.matchTemplate(new_bargain,old_bargain,cv2.TM_CCOEFF_NORMED)
            theight, twidth = old_bargain.shape[:2]
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            x = max_loc[0]
            y = max_loc[1]
            new_bargain = new_bargain[y:y+theight, x:x+twidth]
            result = cv2.matchTemplate(new_bargain,old_bargain,cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            print(f"对比结果:{max_val}")
            if max_val > 0.99:
                # cv2.imwrite("new_bargain.jpg", new_bargain)
                # cv2.imwrite("old_bargain.jpg", old_bargain)
                return False, old_bargain
            else:
                # cv2.imwrite("new_bargain.jpg", new_bargain)
                # cv2.imwrite("old_bargain.jpg", old_bargain)
                return True, new_bargain

        success = 0
        times = 0
        max_bargain_range = False
        old_bargain=cv_imread("picture/"+bargain+"幅度0%.png")
        while success < bargain_success and times < bargain_times and not max_bargain_range:
            if not self.stopped.is_set():
                while not self.paused.is_set():
                    self.paused.wait()
                    if self.stopped.is_set():
                        return
                bargain_location = self.find_template(bargain)
                if bargain_location:
                    if not self.stopped.is_set():
                        while not self.paused.is_set():
                            self.paused.wait()
                            if self.stopped.is_set():
                                return
                        self.check_template(bargain_location, times=2)
                    if self.fatigue_recovery_var:
                        if self.lollipop > 0 or self.gum > 0 or self.lighter > 0 or self.birch_stone > 0:
                            flag = self.physical_power()
                            if flag:
                                continue
                    while not self.stopped.is_set():
                        while not self.paused.is_set():
                            self.paused.wait()
                            if self.stopped.is_set():
                                break
                        bargain_location = self.find_template(bargain)
                        if bargain_location:
                            new_bargain = cv2.imread('picture/screenshot.png')
                            bargain_result, old_bargain = contrast_bargain_range(new_bargain, old_bargain)
                            break
                    if bargain_result:
                        app.update_log("交涉成功")
                        success = success+1
                    else:
                        app.update_log("交涉失败")
                    times = times+1
                    app.update_log(f"{bargain}{times}次，成功{success}次")
                    # time.sleep(1)
                    max_bargain_range = self.find_template("砍价幅度20%", 0.99)
            else:
                break
      
    
    def buy_merchandise(self, merchandises):
        need_merchandises = []
        bought_merchandises = []
        filp=True
        i = 0
        if type(merchandises) is str:
            need_merchandises.append(merchandises)
            filp = False
        else:
            for merchandise, state in merchandises.items():
                if state.get():
                    need_merchandises.append(merchandise)
        while not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            self.take_screenshot()
            for merchandise in need_merchandises:
                if merchandise not in bought_merchandises:
            
                    location = self.find_template("商品/"+merchandise, threshold=0.95)
                    if location:
                        self.check_template(location)
                        app.update_log(f"添加{merchandise}")
                        bought_merchandises.append(merchandise)
                        continue
            
            app.update_log("滑动商品栏")
            if filp:
                self.adb_input_swipe(1020, 1000, 1020, 250)
                i = i+1
                if i%3 == 2:
                    filp = False
            else:
                self.adb_input_swipe(1020, 250, 1020, 1000)
                i = i+1
                if i%3 == 2:
                    filp = True
            if set(bought_merchandises) == set(need_merchandises):
                break
    
    def find_template(self, name, threshold=0.9, take_screenshot=True, base='screenshot', cut=[0, 0]):
        if not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            if take_screenshot:
                self.take_screenshot()
            image = cv_imread('picture/'+base+'.png')
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            #读取模板图片
            template = cv_imread("picture/"+name+".png")
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            #获得模板图片的高宽尺寸
            theight, twidth = template.shape[:2]
            
            template = template[cut[1]:theight-cut[1], cut[0]:twidth-cut[0]]
            theight, twidth = template.shape[:2]
            #执行模板匹配，采用的匹配方式cv2.TM_SQDIFF_NORMED
            result = cv2.matchTemplate(image,template,cv2.TM_CCOEFF_NORMED)
            print(f"开始匹配：{name}")
            #归一化处理
            # cv2.normalize(result, result, 0, 1, cv2.NORM_MINMAX, -1)
            #寻找矩阵（一维数组当做向量，用Mat定义）中的最大值和最小值的匹配结果及其位置
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            print(f"{max_val}:{max_loc}")
            print(f"{twidth}:{theight}")
            if max_val > threshold:
                template_center_location_x = twidth//2+max_loc[0]
                template_center_location_y = theight//2+max_loc[1]
                print(template_center_location_x, " ",template_center_location_y)
                return [template_center_location_x, template_center_location_y]
            else:
                return False



    # 模拟点击操作
    def check_template(self, template_center_location, times=0.5):
        if not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            subprocess.run([adb_path, '-s', f'127.0.0.1:{port}', "shell", "input", "tap", str(template_center_location[0]), str(template_center_location[1])], creationflags=0x08000000)
            time.sleep(times)

    # 模拟滑动操作
    def adb_swipe(self, start_x, start_y, end_x, end_y, duration=500, times=1):
        if not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            command = [adb_path, '-s', f'127.0.0.1:{port}', "shell", "input", "swipe", str(start_x), str(start_y), str(end_x), str(end_y), str(duration)]
            subprocess.run(command, creationflags=0x08000000)
            time.sleep(times)
        
    def adb_input_swipe(self, start_x, start_y, end_x, end_y, times=1):
        if not self.stopped.is_set():
            while not self.paused.is_set():
                self.paused.wait()
                if self.stopped.is_set():
                    break
            command = [adb_path, '-s', f'127.0.0.1:{port}', "shell", "input", 'draganddrop', str(start_x), str(start_y), str(end_x), str(end_y), '500']
            subprocess.run(command, creationflags=0x08000000)
            time.sleep(times)
            
    
    def stop(self):
        self.stopped.set()

    def pause(self):
        self.paused.clear()

    def resume(self):
        self.paused.set()

    def stop_when_finished(self):
        self.i = self.times

class RunAdb(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.app = app

    def run(self) -> None:
        self.connect(self.app)
    
    def run_adb_command(self, command, app):
        """运行ADB命令，并在GUI中更新日志"""
        result = subprocess.run([adb_path] + command, capture_output=True, text=True, creationflags=0x08000000)
        if result.stderr:
            app.update_log("ADB命令执行出错: " + result.stderr)
        elif result.stdout != None:
            app.update_log(result.stdout)
        return result.stdout

    def connect_emulator(self, port="7555", app=None):
        """连接到模拟器，并在GUI中更新日志"""
        return self.run_adb_command(["connect", f"127.0.0.1:{port}"], app)

    def check_connection(self, port="7555", app=None):
        """检查是否已连接到模拟器，并在GUI中更新日志"""
        output = self.run_adb_command(["devices"], app)
        if output != 'outline':
            return f"127.0.0.1:{port}" in output
        else:
            return False
    
    def connect(self, app):
        # connected = False
            global port
        # while not connected:
        # for i in range(4):
            app.update_log("尝试连接到MuMu模拟器...")
            self.connect_emulator(app=app)
            # time.sleep(1)  # 等待一秒
            if self.check_connection(app=app):
                app.update_log("成功连接到MuMu模拟器。")
                # connected = True
            else:
                app.update_log("连接失败")
                app.update_log("尝试连接到雷电模拟器...")
                port = '5555'
                self.connect_emulator(port=port, app=app)
                # time.sleep(1)
                if self.check_connection(port=port, app=app):
                    app.update_log("成功连接到雷电模拟器")
                    # connected = True
                else:
                    app.update_log("连接失败")
                    app.update_log("尝试连接到夜神模拟器...")
                    port = '62001'
                    self.connect_emulator(port=port, app=app)
                    # time.sleep(1)
                    if self.check_connection(port=port, app=app):
                        app.update_log("成功连接到夜神模拟器")
                        # connected = True
                    else:
                        app.update_log("连接失败")


class TradingAssistantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # 读取xlsx文件
        df = pd.read_excel('城市-商品.xlsx', header=None)
        # 将值合并为列表
        data_dict={}
        for index, row in df.iterrows():
            header = row[0]  # 第一列作为表头
            values = row[1:].tolist()  # 其他列作为值，转换为列表
            data_dict[header] = values

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.title("跑商助手")
        self.iconbitmap('picture/gui_ico.ico')
        self.cities = data_dict
        self.create_widgets()
        self.load_settings()


    def create_widgets(self):
        # 创建Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill="both")

        # 创建跑商分页
        trading_frame = ttk.Frame(notebook)
        notebook.add(trading_frame, text="跑商")

        # 跑商分页布局
        log_frame = ttk.Frame(trading_frame)
        control_frame = ttk.Frame(trading_frame)
        log_frame.pack(side="left", fill="both", expand=True)
        control_frame.pack(side="right", fill="y", padx=20)  # 添加内边距，缩小右侧控制区域的宽度)

        # 程序日志
        self.log_text = tk.Text(log_frame, height=20, width=23)  # 使用self来引用log_text，以便在类的其他方法中访问
        self.log_text.pack(expand=True, fill="both")
        self.log_text.config(state=tk.DISABLED)

        # 控制区域
        # 下拉框变量
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        # 第一行 - 下拉框
        ttk.Label(control_frame, text="起点：").grid(row=0, column=0, sticky="w")
        self.start_combobox = ttk.Combobox(control_frame, width=8, state="readonly", textvariable=self.start_var)
        self.start_combobox['values'] = list(self.cities.keys())
        self.start_combobox.grid(row=0, column=1)
        ttk.Label(control_frame, text="终点：").grid(row=0, column=2, sticky="w")
        self.end_combobox = ttk.Combobox(control_frame, width=8, state="readonly", textvariable=self.end_var)
        self.end_combobox['values'] = list(self.cities.keys())
        self.end_combobox.grid(row=0, column=3)

        # 输入框变量
        self.round_trip_times_var = tk.StringVar(value='9999')
        self.lollipop_var = tk.StringVar(value='0')
        self.gum_var = tk.StringVar(value='0')
        self.lighter_var = tk.StringVar(value='0')
        self.birch_stone_var = tk.StringVar(value='0')
        # 为输入框定义验证函数
        vcmd = (self.register(self.on_validate), '%P')
        # 多选框变量
        self.fatigue_recovery_var = tk.BooleanVar()
        self.auto_catch = tk.BooleanVar()
        # 第二行
        ttk.Label(control_frame, text="双程跑商次数").grid(row=1, column=0, sticky="w")
        ttk.Entry(control_frame, width=8, textvariable=self.round_trip_times_var, validate='key', validatecommand=vcmd).grid(row=1, column=1)
        self.round_trip_button = ttk.Button(control_frame, text="双程跑商", width=8, command=self.on_round_trip)
        self.round_trip_button.grid(row=1, column=2)
        self.one_way_button = ttk.Button(control_frame, text="单程跑商", width=8, command=self.on_one_way_trip)
        self.one_way_button.grid(row=1, column=3)

        # 第三行
        self.stop_trading_button = ttk.Button(control_frame, text="停止跑商", width=8, command=self.on_stop_trading)
        self.stop_trading_button.grid(row=2, column=0)
        self.stop_trading_button.config(state=tk.DISABLED)
        self.pause_trading_button = ttk.Button(control_frame, text="暂停跑商", width=8, command=self.on_pause_trading)
        self.pause_trading_button.grid(row=2, column=1)
        self.pause_trading_button.config(state=tk.DISABLED)
        self.resume_trading_button = ttk.Button(control_frame, text="恢复跑商", width=8, command=self.on_resume_trading)
        self.resume_trading_button.grid(row=2, column=2)
        self.resume_trading_button.config(state=tk.DISABLED)
        self.stop_when_finished_button = ttk.Button(control_frame, text="该趟后停止", width=10, command=self.stop_when_finished)
        self.stop_when_finished_button.grid(row=2, column=3)
        self.stop_when_finished_button.config(state=tk.DISABLED)

        # 第四行
        ttk.Label(control_frame, text="提神棒棒糖：").grid(row=3, column=0, sticky="w")
        ttk.Entry(control_frame, width=8, textvariable=self.lollipop_var, validate='key', validatecommand=vcmd).grid(row=3, column=1)
        ttk.Label(control_frame, text="提神口香糖：").grid(row=3, column=2, sticky="w")
        ttk.Entry(control_frame, width=8, textvariable=self.gum_var, validate='key', validatecommand=vcmd).grid(row=3, column=3)
        ttk.Label(control_frame, text="仙人掌提神跳糖：").grid(row=4, column=0, sticky="w")
        ttk.Entry(control_frame, width=8, textvariable=self.lighter_var, validate='key', validatecommand=vcmd).grid(row=4, column=1)
        ttk.Label(control_frame, text="桦石：").grid(row=4, column=2, sticky="w")
        ttk.Entry(control_frame, width=8, textvariable=self.birch_stone_var, validate='key', validatecommand=vcmd).grid(row=4, column=3)
        ttk.Checkbutton(control_frame, text="疲劳恢复", variable=self.fatigue_recovery_var).grid(row=5, column=0)
        self.fatigue_recovery_var.set(False)
        ttk.Checkbutton(control_frame, text="自动拾取", variable=self.auto_catch).grid(row=5, column=1)
        self.auto_catch.set(False)
        # 创建交易所设置分页
        exchange_frame = ttk.Frame(notebook)
        notebook.add(exchange_frame, text="交易所设置")


        # 交易所设置分页的Notebook
        exchange_notebook = ttk.Notebook(exchange_frame)
        exchange_notebook.pack(expand=True, fill="both")
        
        self.merchandise_vars = {}  #商品变量
        self.fill_merchandise_vars = {}  #填补商品变量
        self.bargain_times_vars = {}  # 砍价次数变量
        self.bargain_success_vars = {}  # 砍价成功次数变量
        self.raise_price_times_vars = {}  # 抬价次数变量
        self.raise_price_success_vars = {}  # 抬价成功次数变量
        self.purchase_book_vars = {}  # 进货采买书变量

        # 为每个城市创建一个分页
        for city in self.cities:
            city_frame = ttk.Frame(exchange_notebook)
            exchange_notebook.add(city_frame, text=city)

            # 城市分页布局
            city_left_frame = ttk.Frame(city_frame)
            city_right_frame = ttk.Frame(city_frame)
            city_left_frame.pack(side="left", fill="both", expand=True)
            city_right_frame.pack(side="right", fill="both", expand=True)

            # 城市分页中间的分割线
            separator = ttk.Separator(city_frame, orient='vertical')
            separator.pack(side="left", fill='y', padx=5)

            # 城市分页左侧
            self.merchandise_vars[city] = {}
            self.fill_merchandise_vars[city] = tk.StringVar(value='')
            i=0
            # 将列表转换为Pandas的Series
            cities_series = pd.Series(self.cities[city])
            # 去掉NaN值
            cities_series_cleaned = cities_series.dropna().tolist()
            for i, option in enumerate(cities_series_cleaned):
                if option != 'nan':
                    self.merchandise_vars[city][option] = tk.BooleanVar(value=False)
                    ttk.Checkbutton(city_left_frame, text=option, variable=self.merchandise_vars[city][option]).grid(row=i//2, column=i%2, sticky="w")
            ttk.Label(city_left_frame, text="填补商品").grid(row=(i//2)+1, column=0, sticky="w")
            ttk.Combobox(city_left_frame, width=10, state="readonly", textvariable=self.fill_merchandise_vars[city], values=['']+cities_series_cleaned).grid(row=(i//2)+1, column=1)

        # 城市分页右侧
            self.bargain_times_vars[city] = tk.StringVar(value='0')
            self.bargain_success_vars[city] = tk.StringVar(value='0')
            self.raise_price_times_vars[city] = tk.StringVar(value='0')
            self.raise_price_success_vars[city] = tk.StringVar(value='0')
            self.purchase_book_vars[city] = tk.StringVar(value='0')

            ttk.Label(city_right_frame, text="砍价次数").grid(row=0, column=0, sticky="w")
            ttk.Entry(city_right_frame, width=10, textvariable=self.bargain_times_vars[city], validate='key', validatecommand=vcmd).grid(row=0, column=1)
            ttk.Label(city_right_frame, text="砍价成功次数").grid(row=0, column=2, sticky="w")
            ttk.Entry(city_right_frame, width=10, textvariable=self.bargain_success_vars[city], validate='key', validatecommand=vcmd).grid(row=0, column=3)

            ttk.Label(city_right_frame, text="抬价次数").grid(row=1, column=0, sticky="w")
            ttk.Entry(city_right_frame, width=10, textvariable=self.raise_price_times_vars[city], validate='key', validatecommand=vcmd).grid(row=1, column=1)
            ttk.Label(city_right_frame, text="抬价成功次数").grid(row=1, column=2, sticky="w")
            ttk.Entry(city_right_frame, width=10, textvariable=self.raise_price_success_vars[city], validate='key', validatecommand=vcmd).grid(row=1, column=3)

            ttk.Label(city_right_frame, text="进货采买书").grid(row=2, column=0, sticky="w")
            ttk.Entry(city_right_frame, width=10, textvariable=self.purchase_book_vars[city], validate='key', validatecommand=vcmd).grid(row=2, column=1)

        # 创建自动砍树分页
        # tree_frame = ttk.Frame(notebook)
        # notebook.add(tree_frame, text="自动砍树")

        # self.cactus_pop_var = tk.StringVar(value='0')
        # self.cactus_jump_var = tk.StringVar(value='0')
        # self.cactus_energy_var = tk.StringVar(value='0')
        # self.tree_birch_stone_var = tk.StringVar(value='0')

        # 连接设置分页
        connect_frame = ttk.Frame(notebook)
        notebook.add(connect_frame, text="连接设置")

        connect_log_frame = ttk.Frame(connect_frame)
        connect_control_frame = ttk.Frame(connect_frame)
        connect_log_frame.pack(side="left", fill="both", expand=True)
        connect_control_frame.pack(side="right", fill="y", padx=20)  # 添加内边距，缩小右侧控制区域的宽度)

        # 程序日志
        self.connect_log_text = tk.Text(connect_log_frame, height=20, width=23)  # 使用self来引用log_text，以便在类的其他方法中访问
        self.connect_log_text.pack(expand=True, fill="both")
        self.connect_log_text.config(state=tk.DISABLED)

        self.adb_location = tk.StringVar()
        ttk.Label(connect_control_frame, text="adb所在目录:").grid(row=0, column=0, sticky="w")
        ttk.Entry(connect_control_frame, width=40, textvariable=self.adb_location, validate='key').grid(row=0, column=1)
        self.connect_adb_button = ttk.Button(connect_control_frame, text="重新连接adb", width=10, command=self.connect_adb)
        self.connect_adb_button.grid(row=1, column=0)

    
    def connect_adb(self):
        global adb_path
        try:
            subprocess.run([adb_path, "disconnect"], check=True)
            print("当前ADB连接已断开。")
            self.update_log("当前ADB连接已断开。\n")
        except subprocess.CalledProcessError as e:
            print(f"Error disconnecting ADB: {e}")
        
        adb_location = self.adb_location.get()
        if adb_location == '':
            self.update_log("文本框内为空，使用默认adb路径。")
            adb_location = 'adb'
        adb_path = os.path.join(adb_location, 'adb.exe')
        print(adb_path)
        adb = RunAdb(self)
        adb.start()
        

    def on_validate(self, P):
        """验证函数，只允许输入数字"""
        if P.strip() == "" or P.isdigit():
            return True
        return False

    def on_round_trip(self):
        """处理双程跑商按钮点击"""
        start = self.start_combobox.get()
        end = self.end_combobox.get()
        times = self.round_trip_times_var.get()
        lollipop = self.lollipop_var.get()
        gum = self.gum_var.get()
        lighter = self.lighter_var.get()
        birch_stone = self.birch_stone_var.get()
        fatigue_recovery_var = self.fatigue_recovery_var.get()
        if start == '' or end == '':
            self.update_log("起点或终点请勿为空")
        else:
            self.update_log(f"起点：{start}\n终点：{end}\n往返次数：{times}次\n")
            # 将跑商按钮设置为不可点击
            self.round_trip_button.config(state=tk.DISABLED)
            self.one_way_button.config(state=tk.DISABLED)
            # 将其他按钮设置为可点击
            self.stop_trading_button.config(state=tk.NORMAL)
            self.pause_trading_button.config(state=tk.NORMAL)
            self.stop_when_finished_button.config(state=tk.NORMAL)
            global trading_thread
            trading_thread = TradingThread(start, end, times, lollipop, gum, lighter, birch_stone, fatigue_recovery_var)
            trading_thread.start()

    def on_one_way_trip(self):
        """处理单程跑商按钮点击"""
        start = self.start_combobox.get()
        end = self.end_combobox.get()
        lollipop = self.lollipop_var.get()
        gum = self.gum_var.get()
        lighter = self.lighter_var.get()
        birch_stone = self.birch_stone_var.get()
        fatigue_recovery_var = self.fatigue_recovery_var.get()
        if start == '' or end == '':
            self.update_log("起点或终点请勿为空")
        else:
            self.update_log(f"起点：{start}\n终点：{end}\n")
            # 将跑商按钮设置为不可点击
            self.round_trip_button.config(state=tk.DISABLED)
            self.one_way_button.config(state=tk.DISABLED)
            # 将其他按钮设置为可点击
            self.stop_trading_button.config(state=tk.NORMAL)
            self.pause_trading_button.config(state=tk.NORMAL)
            self.stop_when_finished_button.config(state=tk.NORMAL)
            global trading_thread
            trading_thread = TradingThread(start, end, 1, lollipop, gum, lighter, birch_stone, fatigue_recovery_var)
            trading_thread.start()

    def on_stop_trading(self):
        """处理停止跑商按钮点击"""
        self.update_log("停止跑商\n")
        trading_thread.resume()
        trading_thread.stop()
        if 'catch_rubbish' in globals():
            if catch_rubbish.is_alive():
                catch_rubbish.resume()
                catch_rubbish.stop()
        # trading_thread.join()
        self.stop_trading_button.config(state=tk.DISABLED)
        self.pause_trading_button.config(state=tk.DISABLED)
        self.resume_trading_button.config(state=tk.DISABLED)
        self.stop_when_finished_button.config(state=tk.DISABLED)
        self.round_trip_button.config(state=tk.NORMAL)
        self.one_way_button.config(state=tk.NORMAL)
        
        

    def on_pause_trading(self):
        """处理暂停跑商按钮点击"""
        self.update_log("暂停跑商\n")
        trading_thread.pause()
        if 'catch_rubbish' in globals():
            if catch_rubbish.is_alive():
                catch_rubbish.pause()
        self.pause_trading_button.config(state=tk.DISABLED)
        self.resume_trading_button.config(state=tk.NORMAL)
        

    def on_resume_trading(self):
        """处理恢复跑商按钮点击"""
        self.update_log("恢复跑商\n")
        trading_thread.resume()
        if 'catch_rubbish' in globals():
            if catch_rubbish.is_alive():
                catch_rubbish.resume()
        self.pause_trading_button.config(state=tk.NORMAL)
        self.resume_trading_button.config(state=tk.DISABLED)

    def stop_when_finished(self):
        """处理该趟后停止按钮点击"""
        if 'trading_thread' in globals():
            if trading_thread.is_alive():
                self.update_log("完成此次跑商后停止跑商\n")
                trading_thread.stop_when_finished()
                self.stop_when_finished_button.config(state=tk.DISABLED)
        
    
    def update_log(self, message):
        """更新日志显示框的内容"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        self.connect_log_text.config(state=tk.NORMAL)
        self.connect_log_text.insert(tk.END, message + "\n")
        self.connect_log_text.see(tk.END)
        self.connect_log_text.config(state=tk.DISABLED)
    
    def save_settings(self):
        settings = {
            'adb_path': self.adb_location.get(),
            'start_city': self.start_var.get(),
            'end_city': self.end_var.get(),
            'round_trip_times': self.round_trip_times_var.get(),
            'lollipop': self.lollipop_var.get(),
            'gum': self.gum_var.get(),
            'lighter': self.lighter_var.get(),
            'birch_stone': self.birch_stone_var.get(),
            'fatigue_recovery': self.fatigue_recovery_var.get(),

            'merchandise': {city: {item: var.get() for item, var in city_vars.items()} for city, city_vars in self.merchandise_vars.items()},
            'fill_merchandise': {city: var.get() for city, var in self.fill_merchandise_vars.items()},

            'bargain_times': {city: var.get() for city, var in self.bargain_times_vars.items()},
            'bargain_success': {city: var.get() for city, var in self.bargain_success_vars.items()},
            'raise_price_times': {city: var.get() for city, var in self.raise_price_times_vars.items()},
            'raise_price_success': {city: var.get() for city, var in self.raise_price_success_vars.items()},
            'purchase_book':{city: var.get() for city, var in self.purchase_book_vars.items()},
        }
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f)
    
    def load_settings(self):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.adb_location.set(settings.get('adb_path', ''))
                global adb_path
                if settings.get('adb_path', '') != '':
                    adb_path = os.path.join(settings.get('adb_path', ''), 'adb.exe')
                else:
                    adb_path = os.path.join('adb', 'adb.exe')
                self.start_var.set(settings.get('start_city', ''))
                self.end_var.set(settings.get('end_city', ''))
                self.round_trip_times_var.set(settings.get('round_trip_times', ''))
                self.lollipop_var.set(settings.get('lollipop', ''))
                self.gum_var.set(settings.get('gum', ''))
                self.lighter_var.set(settings.get('lighter', ''))
                self.birch_stone_var.set(settings.get('birch_stone', ''))
                self.fatigue_recovery_var.set(settings.get('fatigue_recovery', ''))

                # 设置商品状态
                for city, city_vars in self.merchandise_vars.items():
                    self.fill_merchandise_vars[city].set(settings.get('fill_merchandise', '')[city])
                    for item, var in city_vars.items():
                        var.set(settings['merchandise'].get(city, {}).get(item, False))

                for city in self.cities.keys():
                    if city in self.bargain_times_vars:
                        self.bargain_times_vars[city].set(settings.get('bargain_times', '')[city])
                    if city in self.bargain_success_vars:
                        self.bargain_success_vars[city].set(settings.get('bargain_success', '')[city])
                    if city in self.raise_price_times_vars:
                        self.raise_price_times_vars[city].set(settings.get('raise_price_times', '')[city])
                    if city in self.raise_price_success_vars:
                        self.raise_price_success_vars[city].set(settings.get('raise_price_success', '')[city])
                    if city in self.purchase_book_vars:
                        self.purchase_book_vars[city].set(settings.get('purchase_book', '')[city])
        except FileNotFoundError:
            pass  # 文件不存在时忽略错误
    
    def on_close(self):
        if 'trading_thread' in globals():
            if trading_thread.is_alive():
                trading_thread.resume()
                trading_thread.stop()
        if 'catch_rubbish' in globals():
            if catch_rubbish.is_alive():
                catch_rubbish.resume()
                catch_rubbish.stop()
        self.save_settings()
        self.destroy()

        

app = TradingAssistantApp()
app.update_log("注意：使用跑商助手时请将模拟器分辨率设置为1920*1080，并将游戏分辨率设置为高，否则跑商助手将无法正常工作。")
adb_path = os.path.join('adb', 'adb.exe')
adb = RunAdb(app)
adb.start()
app.mainloop()