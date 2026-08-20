# 跑商助手

界面基于 [CustomTkinter](https://customtkinter.tomschimansky.com/)，风格简洁现代。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动

```bash
python gui_picture.py
```

## 目录结构

```
gui_picture.py           # 程序入口
config.py                # 路径与默认配置
state.py                 # 运行时共享状态
adb_ops/                 # ADB 命令与模拟器连接（非依赖目录 adb/）
vision/                  # 模板匹配
workers/                 # 跑商 / 拾取等后台线程
gui/                     # Tkinter 界面与设置读写
data/                    # 城市-商品表加载
utils/                   # 通用工具（如中文路径读图）
adb/                     # ADB 依赖（无需修改）
picture/                 # 模板图片资源
城市-商品.xlsx
```
