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

## 更新（面向封装版用户）

在「连接设置」页点击 **更新程序**：

1. 检查 GitHub Releases 最新版本标签
2. 下载 Release 中的 **zip 封装包**（内含 exe 等文件）
3. 同步改动文件，并删除弃用文件
4. 本地 `settings.json` 与 `adb/` 不会被覆盖或删除

发布 Release 时请上传 `.zip` 资源；若正在运行的 exe 无法直接覆盖，程序会退出并由脚本自动完成替换后重启。

仓库：[`JYmao-10086/ResonanceAutoScript`](https://github.com/JYmao-10086/ResonanceAutoScript)

## 目录结构

```
gui_picture.py           # 程序入口
config.py                # 路径与默认配置
state.py                 # 运行时共享状态
adb_ops/                 # ADB 命令与模拟器连接（非依赖目录 adb/）
vision/                  # 模板匹配
workers/                 # 跑商 / 拾取等后台线程
gui/                     # 界面与设置读写
data/                    # 城市-商品表加载
utils/                   # 通用工具（读图、Release 更新）
adb/                     # ADB 依赖（无需修改）
picture/                 # 模板图片资源
城市-商品.xlsx
```
