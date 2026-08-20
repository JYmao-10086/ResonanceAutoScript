"""从 GitHub Releases 检查并同步封装版更新（zip 内 exe 等文件）。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from typing import Callable, Optional, Set
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import ROOT_DIR

GITHUB_OWNER = "JYmao-10086"
GITHUB_REPO = "ResonanceAutoScript"
VERSION_FILE_NAME = ".app_version"

API_LATEST_RELEASE_URL = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)

# 更新时保留的本地内容
PROTECTED_EXACT = {
    "settings.json",
    VERSION_FILE_NAME,
}
PROTECTED_PREFIXES = (
    "adb/",
    ".git/",
    "__pycache__/",
)
PROTECTED_SUFFIXES = (
    ".pyc",
    ".pyo",
)
PROTECTED_NAMES = {
    "screenshot.png",
}


ProgressCb = Callable[[str], None]


def get_app_root() -> str:
    """安装/运行目录：封装 exe 用可执行文件所在目录，源码运行用项目根目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return ROOT_DIR


def version_file_path() -> str:
    return os.path.join(get_app_root(), VERSION_FILE_NAME)


@dataclass
class UpdateCheckResult:
    has_update: bool
    local_tag: str = ""
    remote_tag: str = ""
    release_name: str = ""
    release_notes: str = ""
    asset_name: str = ""
    asset_url: str = ""
    asset_size: int = 0
    error: str = ""


@dataclass
class ApplyResult:
    ok: bool
    updated: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    error: str = ""
    restart_required: bool = False
    restart_exe: str = ""


def _http_get(url: str, timeout: int = 30) -> bytes:
    req = Request(
        url,
        headers={
            "User-Agent": "ResonanceAutoScript-Updater",
            "Accept": "application/vnd.github+json",
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _http_download(url: str, dest: str, timeout: int = 300, progress: Optional[ProgressCb] = None) -> None:
    req = Request(
        url,
        headers={
            "User-Agent": "ResonanceAutoScript-Updater",
            "Accept": "application/octet-stream",
        },
    )
    with urlopen(req, timeout=timeout) as resp, open(dest, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        last_pct = -1
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if progress and total > 0:
                pct = int(done * 100 / total)
                if pct >= last_pct + 10 or pct == 100:
                    last_pct = pct
                    progress(f"下载进度：{pct}%（{done // (1024 * 1024)} MB）")


def read_local_tag() -> str:
    try:
        with open(version_file_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return str(data.get("tag", data.get("sha", ""))).strip()
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return ""


def write_local_version(tag: str, release_name: str = "", asset_name: str = "") -> None:
    payload = {
        "tag": tag,
        "name": release_name,
        "asset": asset_name,
        "repo": f"{GITHUB_OWNER}/{GITHUB_REPO}",
    }
    with open(version_file_path(), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def is_protected(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/").lstrip("./")
    if not norm or norm in PROTECTED_EXACT:
        return True
    if any(norm.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return True
    if any(norm.endswith(suffix) for suffix in PROTECTED_SUFFIXES):
        return True
    name = norm.rsplit("/", 1)[-1]
    if name in PROTECTED_NAMES:
        return True
    if "__pycache__" in norm.split("/"):
        return True
    return False


def iter_files(root: str) -> Set[str]:
    result: Set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = ""
        dirnames[:] = [
            d
            for d in dirnames
            if not is_protected(f"{rel_dir}/{d}".lstrip("/") + "/")
            and d not in {".git", "__pycache__", "adb"}
        ]
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root).replace("\\", "/")
            if not is_protected(rel):
                result.add(rel)
    return result


def _pick_release_asset(assets: list) -> Optional[dict]:
    """优先选择 zip 压缩包资源。"""
    zips = [
        a
        for a in assets
        if str(a.get("name", "")).lower().endswith(".zip") and a.get("browser_download_url")
    ]
    if not zips:
        # 兼容 rar/7z 提示失败，先只支持 zip
        return None
    # 同名优先含 win/release/dist 的，否则取体积最大
    preferred = [
        a
        for a in zips
        if any(k in str(a.get("name", "")).lower() for k in ("win", "release", "dist", "exe", "跑商"))
    ]
    pool = preferred or zips
    return max(pool, key=lambda a: int(a.get("size") or 0))


def check_for_update(progress: Optional[ProgressCb] = None) -> UpdateCheckResult:
    def log(msg: str) -> None:
        if progress:
            progress(msg)

    log("正在连接 GitHub Releases 检查更新...")
    local_tag = read_local_tag()
    try:
        raw = _http_get(API_LATEST_RELEASE_URL)
        data = json.loads(raw.decode("utf-8"))
        remote_tag = str(data.get("tag_name", "")).strip()
        release_name = str(data.get("name") or remote_tag).strip()
        body = str(data.get("body") or "").strip()
        notes = body.splitlines()[0] if body else release_name
        assets = data.get("assets") or []
        asset = _pick_release_asset(assets)
        if not remote_tag:
            return UpdateCheckResult(False, local_tag, error="无法解析 Release 版本号")
        if not asset:
            return UpdateCheckResult(
                False,
                local_tag,
                remote_tag=remote_tag,
                release_name=release_name,
                release_notes=notes,
                error="最新 Release 中未找到 zip 更新包，请确认已上传封装压缩包",
            )
        asset_name = str(asset.get("name", ""))
        asset_url = str(asset.get("browser_download_url", ""))
        asset_size = int(asset.get("size") or 0)
        if local_tag and local_tag == remote_tag:
            return UpdateCheckResult(
                False,
                local_tag=local_tag,
                remote_tag=remote_tag,
                release_name=release_name,
                release_notes=notes,
                asset_name=asset_name,
                asset_url=asset_url,
                asset_size=asset_size,
            )
        return UpdateCheckResult(
            True,
            local_tag=local_tag,
            remote_tag=remote_tag,
            release_name=release_name,
            release_notes=notes,
            asset_name=asset_name,
            asset_url=asset_url,
            asset_size=asset_size,
        )
    except HTTPError as e:
        if e.code == 404:
            return UpdateCheckResult(
                False,
                local_tag,
                error="未找到 Release（仓库无发行版或仓库不可访问）",
            )
        return UpdateCheckResult(False, local_tag, error=f"GitHub API 错误: HTTP {e.code}")
    except URLError as e:
        return UpdateCheckResult(False, local_tag, error=f"网络错误: {e.reason}")
    except Exception as e:  # noqa: BLE001
        return UpdateCheckResult(False, local_tag, error=f"检查更新失败: {e}")


def _resolve_extract_root(extract_dir: str) -> str:
    """若压缩包只有一层目录则进入该目录。"""
    entries = [n for n in os.listdir(extract_dir) if n not in {"source.zip", "__MACOSX"}]
    dirs = [n for n in entries if os.path.isdir(os.path.join(extract_dir, n))]
    files = [n for n in entries if os.path.isfile(os.path.join(extract_dir, n))]
    if len(dirs) == 1 and not files:
        return os.path.join(extract_dir, dirs[0])
    return extract_dir


def _download_and_extract(asset_url: str, progress: Optional[ProgressCb] = None) -> tuple[str, str]:
    def log(msg: str) -> None:
        if progress:
            progress(msg)

    temp_dir = tempfile.mkdtemp(prefix="ras_release_")
    zip_path = os.path.join(temp_dir, "release.zip")
    log("正在下载 Release 更新包...")
    _http_download(asset_url, zip_path, progress=progress)
    log("正在解压更新包...")
    extract_dir = os.path.join(temp_dir, "extracted")
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    return temp_dir, _resolve_extract_root(extract_dir)


def _running_exe_rel(app_root: str) -> Optional[str]:
    if not getattr(sys, "frozen", False):
        return None
    exe_path = os.path.abspath(sys.executable)
    try:
        rel = os.path.relpath(exe_path, app_root).replace("\\", "/")
    except ValueError:
        return None
    if rel.startswith(".."):
        return None
    return rel


def _copy_file(src: str, dst: str) -> None:
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    shutil.copy2(src, dst)


def _write_restart_script(app_root: str, staging_root: str, exe_name: str) -> str:
    """生成用于替换占用中 exe 的批处理，返回脚本路径。"""
    script = os.path.join(app_root, "_apply_update.bat")
    # 用短路径风格，避免中文引号问题；统一用引号包裹
    content = f"""@echo off
chcp 65001 >nul
set "SRC={staging_root}"
set "DST={app_root}"
set "EXE={exe_name}"
echo 正在应用更新，请稍候...
timeout /t 2 /nobreak >nul
xcopy /E /Y /I /Q "%SRC%\\*" "%DST%\\" >nul
if exist "%DST%\\%EXE%" start "" "%DST%\\%EXE%"
rd /s /q "%SRC%"
del "%~f0"
"""
    with open(script, "w", encoding="gbk", errors="replace") as f:
        f.write(content)
    return script


def apply_update(
    check: UpdateCheckResult,
    progress: Optional[ProgressCb] = None,
) -> ApplyResult:
    def log(msg: str) -> None:
        if progress:
            progress(msg)

    if not check.asset_url:
        return ApplyResult(False, error="缺少 Release 下载地址")

    app_root = get_app_root()
    temp_dir = ""
    staging_keep = ""
    try:
        temp_dir, remote_root = _download_and_extract(check.asset_url, progress)
        remote_files = iter_files(remote_root)
        local_files = iter_files(app_root)
        running_rel = _running_exe_rel(app_root)

        to_update = sorted(remote_files)
        to_delete = sorted(local_files - remote_files)
        updated: list[str] = []
        deleted: list[str] = []
        locked_files: list[str] = []

        log(
            f"开始同步 Release {check.remote_tag}："
            f"更新 {len(to_update)} 个文件，删除 {len(to_delete)} 个弃用文件..."
        )

        for rel in to_update:
            if is_protected(rel):
                continue
            src = os.path.join(remote_root, rel.replace("/", os.sep))
            dst = os.path.join(app_root, rel.replace("/", os.sep))
            try:
                # 正在运行的 exe 通常无法覆盖
                if running_rel and rel.lower() == running_rel.lower():
                    raise PermissionError("running executable")
                _copy_file(src, dst)
                updated.append(rel)
            except OSError:
                locked_files.append(rel)

        for rel in to_delete:
            if is_protected(rel):
                continue
            if running_rel and rel.lower() == running_rel.lower():
                continue
            path = os.path.join(app_root, rel.replace("/", os.sep))
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    deleted.append(rel)
                except OSError:
                    locked_files.append(rel)
                parent = os.path.dirname(path)
                while parent and parent.startswith(app_root) and parent != app_root:
                    try:
                        os.rmdir(parent)
                    except OSError:
                        break
                    parent = os.path.dirname(parent)

        write_local_version(check.remote_tag, check.release_name, check.asset_name)

        if locked_files:
            # 将完整远端内容放到 staging，退出后用脚本覆盖（含 exe）
            staging_keep = tempfile.mkdtemp(prefix="ras_staging_", dir=app_root)
            for rel in to_update:
                if is_protected(rel):
                    continue
                src = os.path.join(remote_root, rel.replace("/", os.sep))
                dst = os.path.join(staging_keep, rel.replace("/", os.sep))
                _copy_file(src, dst)
            exe_name = os.path.basename(sys.executable) if running_rel else ""
            if not exe_name:
                # 找包内主 exe
                exes = [f for f in to_update if f.lower().endswith(".exe") and "/" not in f]
                exe_name = exes[0] if exes else ""
            script = _write_restart_script(app_root, staging_keep, exe_name)
            log("部分文件被占用，将关闭程序后自动完成替换。")
            subprocess.Popen(["cmd", "/c", script], cwd=app_root, creationflags=0x00000008)
            return ApplyResult(
                True,
                updated=updated,
                deleted=deleted,
                restart_required=True,
                restart_exe=exe_name,
            )

        log("更新完成，请重启程序使全部改动生效。")
        return ApplyResult(True, updated=updated, deleted=deleted)
    except HTTPError as e:
        return ApplyResult(False, error=f"下载失败: HTTP {e.code}")
    except URLError as e:
        return ApplyResult(False, error=f"网络错误: {e.reason}")
    except zipfile.BadZipFile:
        return ApplyResult(False, error="更新包不是有效的 zip 文件")
    except Exception as e:  # noqa: BLE001
        return ApplyResult(False, error=f"更新失败: {e}")
    finally:
        if temp_dir and os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def format_tag(tag: str) -> str:
    return tag if tag else "未记录"


def format_size(num: int) -> str:
    if num <= 0:
        return "未知大小"
    mb = num / (1024 * 1024)
    if mb < 1:
        return f"{num / 1024:.0f} KB"
    return f"{mb:.1f} MB"
