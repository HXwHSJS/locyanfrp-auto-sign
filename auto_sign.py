import json
import logging
import os
import sys
import time
import hashlib
import base64
import subprocess
import msvcrt
import tkinter as tk
from tkinter import messagebox
import winsound
from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests

# =========================
# 基础配置
# =========================
API_BASES = [
    "https://api.locyanfrp.cn/v3",
    "https://backup.api.locyanfrp.cn/v3",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOCK_PATH = os.path.join(BASE_DIR, "auto_sign.lock")
LOG_PATH = os.path.join(LOG_DIR, "auto_sign.log")
STATUS_PATH = os.path.join(BASE_DIR, "last_status.json")

TIMEOUT = 15
DEFAULT_TRAFFIC_UNIT = "GB"

logger = logging.getLogger("locyan_sign")


# =========================
# 日志
# =========================
def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)

    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler = RotatingFileHandler(
        LOG_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def log_runtime_info():
    script_path = os.path.abspath(__file__)
    with open(script_path, "rb") as f:
        sha1 = hashlib.sha1(f.read()).hexdigest()

    logger.info("Python: %s", sys.executable)
    logger.info("Script: %s", script_path)
    logger.info("Script SHA1: %s", sha1)
    logger.info("CWD: %s", os.getcwd())
    logger.info("Config: %s", CONFIG_PATH)
    logger.info("Log: %s", LOG_PATH)
    logger.info("Status: %s", STATUS_PATH)


# =========================
# 单实例锁，避免并发运行
# =========================
class SingleInstanceLock:
    def __init__(self, path):
        self.path = path
        self.fp = None

    def acquire(self):
        self.fp = open(self.path, "a+")
        try:
            self.fp.seek(0)
            msvcrt.locking(self.fp.fileno(), msvcrt.LK_NBLCK, 1)
            self.fp.seek(0)
            self.fp.truncate()
            self.fp.write(str(os.getpid()))
            self.fp.flush()
            return True
        except OSError:
            return False

    def release(self):
        if self.fp:
            try:
                self.fp.seek(0)
                msvcrt.locking(self.fp.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
            self.fp.close()
            self.fp = None


# =========================
# 配置读取
# =========================
def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"找不到配置文件: {CONFIG_PATH}。请先将 config.example.json 复制为 config.json 并填写配置。")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    app_id = str(data.get("app_id", "")).strip()
    refresh_token = str(data.get("refresh_token", "")).strip()

    if not app_id:
        raise ValueError("config.json 中缺少 app_id")
    if not refresh_token:
        raise ValueError("config.json 中缺少 refresh_token")

    return {
        "app_id": app_id,
        "refresh_token": refresh_token,
        "traffic_unit": str(data.get("traffic_unit", DEFAULT_TRAFFIC_UNIT)).strip() or DEFAULT_TRAFFIC_UNIT,
        "notify_on_success": bool(data.get("notify_on_success", True)),
        "notify_on_already_signed": bool(data.get("notify_on_already_signed", False)),
        "notify_on_failure": bool(data.get("notify_on_failure", True)),
        "popup_right_margin": int(data.get("popup_right_margin", 20)),
        "popup_top": int(data.get("popup_top", 40)),
        "popup_stack_gap": int(data.get("popup_stack_gap", 10)),
        "popup_success_width": int(data.get("popup_success_width", 400)),
        "popup_success_height": int(data.get("popup_success_height", 100)),
        "popup_error_width": int(data.get("popup_error_width", 470)),
        "popup_error_height": int(data.get("popup_error_height", 130)),
        "persistent_error_width": int(data.get("persistent_error_width", 620)),
        "persistent_error_height": int(data.get("persistent_error_height", 340)),
    }


# =========================
# 请求工具
# =========================
def build_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "LocyanFrpAutoSignTemplate/1.0 (Windows Task Scheduler)",
        "Accept": "application/json",
    })
    return s


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {
            "status": resp.status_code,
            "message": f"Non-JSON response: {resp.text[:500]}",
            "data": {}
        }


# =========================
# 状态文件
# =========================
def write_status(result, message, extra=None):
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result,
        "message": message,
    }
    if extra is not None:
        data["extra"] = extra

    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# 提示窗口
# =========================
def get_helper_python_executable():
    current = sys.executable
    dirname = os.path.dirname(current)
    basename = os.path.basename(current).lower()

    if basename == "python.exe":
        pythonw = os.path.join(dirname, "pythonw.exe")
        if os.path.exists(pythonw):
            return pythonw

    return current


def open_path(path):
    try:
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showwarning("找不到文件", path)
    except Exception as e:
        messagebox.showerror("打开失败", str(e))


def run_popup_notification_window(title, message, kind, cfg):
    try:
        if kind == "error":
            try:
                winsound.MessageBeep(winsound.MB_ICONHAND)
            except Exception:
                pass

        root = tk.Tk()
        root.withdraw()

        win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)

        if kind == "error":
            bg = "#fff1f0"
            fg = "#a8071a"
            border = "#ff4d4f"
            duration_ms = 12000
            width = cfg["popup_error_width"]
            height = cfg["popup_error_height"]
        else:
            bg = "#f6ffed"
            fg = "#237804"
            border = "#52c41a"
            duration_ms = 3500
            width = cfg["popup_success_width"]
            height = cfg["popup_success_height"]

        screen_w = win.winfo_screenwidth()
        x = screen_w - width - cfg["popup_right_margin"]
        y = cfg["popup_top"]

        win.geometry(f"{width}x{height}+{x}+{y}")
        win.configure(bg=border)

        frame = tk.Frame(win, bg=bg)
        frame.place(x=2, y=2, relwidth=1, relheight=1, width=-4, height=-4)

        title_label = tk.Label(
            frame,
            text=title,
            bg=bg,
            fg=fg,
            font=("Microsoft YaHei UI", 11, "bold"),
            anchor="w"
        )
        title_label.pack(fill="x", padx=12, pady=(10, 4))

        msg_label = tk.Label(
            frame,
            text=message,
            bg=bg,
            fg=fg,
            font=("Microsoft YaHei UI", 10),
            justify="left",
            anchor="nw",
            wraplength=width - 30
        )
        msg_label.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        def close_all():
            try:
                win.destroy()
            except Exception:
                pass
            try:
                root.destroy()
            except Exception:
                pass

        win.after(duration_ms, close_all)
        root.mainloop()
    except Exception:
        pass


def launch_popup_notification(title, message, kind, cfg):
    try:
        helper_python = get_helper_python_executable()
        encoded_title = base64.urlsafe_b64encode(title.encode("utf-8")).decode("ascii")
        encoded_message = base64.urlsafe_b64encode(message.encode("utf-8")).decode("ascii")
        encoded_cfg = base64.urlsafe_b64encode(json.dumps(cfg, ensure_ascii=False).encode("utf-8")).decode("ascii")

        cmd = [
            helper_python,
            os.path.abspath(__file__),
            "--popup-window",
            kind,
            encoded_title,
            encoded_message,
            encoded_cfg,
        ]

        kwargs = {"close_fds": True}
        if os.name == "nt" and hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(cmd, **kwargs)
        return True
    except Exception:
        return False


def run_persistent_error_window(message, cfg):
    try:
        try:
            winsound.MessageBeep(winsound.MB_ICONHAND)
        except Exception:
            pass

        root = tk.Tk()
        root.title("LoCyanFrp 自动签到失败")
        root.geometry(f"{cfg['persistent_error_width']}x{cfg['persistent_error_height']}")
        root.minsize(560, 300)
        root.configure(bg="#fff1f0")
        root.attributes("-topmost", True)

        screen_w = root.winfo_screenwidth()
        x = screen_w - cfg["persistent_error_width"] - cfg["popup_right_margin"]
        y = cfg["popup_top"] + cfg["popup_error_height"] + cfg["popup_stack_gap"]
        root.geometry(f"{cfg['persistent_error_width']}x{cfg['persistent_error_height']}+{x}+{y}")

        outer = tk.Frame(root, bg="#ff4d4f", padx=2, pady=2)
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        frame = tk.Frame(outer, bg="#fff1f0")
        frame.pack(fill="both", expand=True)

        title_label = tk.Label(
            frame,
            text="LoCyanFrp 自动签到失败",
            bg="#fff1f0",
            fg="#a8071a",
            font=("Microsoft YaHei UI", 14, "bold"),
            anchor="w"
        )
        title_label.pack(fill="x", padx=16, pady=(16, 6))

        sub_label = tk.Label(
            frame,
            text="右上角短提示已发出。这个窗口会保持显示，直到你手动关闭。",
            bg="#fff1f0",
            fg="#ad4e00",
            font=("Microsoft YaHei UI", 9),
            anchor="w"
        )
        sub_label.pack(fill="x", padx=16, pady=(0, 10))

        text_box = tk.Text(
            frame,
            height=8,
            wrap="word",
            bg="#fffafa",
            fg="#5c0011",
            font=("Consolas", 10),
            relief="solid",
            bd=1
        )
        text_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        text_box.insert("1.0", message)
        text_box.config(state="disabled")

        info_label = tk.Label(
            frame,
            text=f"日志: {LOG_PATH}\n状态文件: {STATUS_PATH}",
            bg="#fff1f0",
            fg="#595959",
            font=("Microsoft YaHei UI", 9),
            justify="left",
            anchor="w"
        )
        info_label.pack(fill="x", padx=16, pady=(0, 10))

        btn_frame = tk.Frame(frame, bg="#fff1f0")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))

        tk.Button(btn_frame, text="打开日志", width=12, command=lambda: open_path(LOG_PATH)).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="打开状态文件", width=12, command=lambda: open_path(STATUS_PATH)).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="打开脚本目录", width=12, command=lambda: open_path(BASE_DIR)).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="关闭", width=12, command=root.destroy).pack(side="right")

        root.mainloop()
    except Exception:
        pass


def launch_persistent_error_window(message, cfg):
    try:
        helper_python = get_helper_python_executable()
        encoded_message = base64.urlsafe_b64encode(message.encode("utf-8")).decode("ascii")
        encoded_cfg = base64.urlsafe_b64encode(json.dumps(cfg, ensure_ascii=False).encode("utf-8")).decode("ascii")

        cmd = [
            helper_python,
            os.path.abspath(__file__),
            "--error-window",
            encoded_message,
            encoded_cfg,
        ]

        kwargs = {"close_fds": True}
        if os.name == "nt" and hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(cmd, **kwargs)
        return True
    except Exception:
        return False


def notify_success(message, cfg):
    if cfg["notify_on_success"]:
        launch_popup_notification("LoCyanFrp 自动签到", message, "success", cfg)


def notify_already_signed(message, cfg):
    if cfg["notify_on_already_signed"]:
        launch_popup_notification("LoCyanFrp 自动签到", message, "success", cfg)


def notify_failure(message, cfg):
    if cfg["notify_on_failure"]:
        launch_popup_notification("LoCyanFrp 自动签到失败", message, "error", cfg)
        time.sleep(0.15)
        launch_persistent_error_window(message, cfg)


# =========================
# OAuth & 签到接口
# =========================
def get_access_token(session, api_base, app_id, refresh_token):
    url = f"{api_base}/auth/oauth/access-token"
    resp = session.post(
        url,
        data={
            "app_id": app_id,
            "refresh_token": refresh_token,
        },
        timeout=TIMEOUT,
    )
    data = safe_json(resp)

    if resp.status_code == 200 and data.get("status") == 200:
        token_data = data.get("data", {})
        access_token = token_data.get("access_token")
        user_id = token_data.get("user_id")
        if access_token and user_id is not None:
            return access_token, user_id

    raise RuntimeError(f"获取 access_token 失败: HTTP {resp.status_code}, 响应: {data}")


def get_sign_status(session, api_base, access_token, user_id):
    url = f"{api_base}/sign"
    resp = session.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        params={"user_id": user_id},
        timeout=TIMEOUT,
    )
    return resp.status_code, safe_json(resp)


def post_sign(session, api_base, access_token, user_id):
    url = f"{api_base}/sign"
    resp = session.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"user_id": user_id},
        timeout=TIMEOUT,
    )
    return resp.status_code, safe_json(resp)


def extract_total_value(data):
    if not isinstance(data, dict):
        return None
    return data.get("total_get_traffic", data.get("total_sign"))


# =========================
# 业务逻辑
# =========================
def try_sign_once(session, api_base, app_id, refresh_token, cfg):
    logger.info("正在使用 API: %s", api_base)

    access_token, user_id = get_access_token(session, api_base, app_id, refresh_token)
    logger.info("获取 access_token 成功，user_id=%s", user_id)

    status_code, status_json = get_sign_status(session, api_base, access_token, user_id)

    if status_code == 401:
        logger.warning("查询签到状态返回 401，重新获取 token 后重试一次")
        access_token, user_id = get_access_token(session, api_base, app_id, refresh_token)
        status_code, status_json = get_sign_status(session, api_base, access_token, user_id)

    if status_code == 200 and status_json.get("status") == 200:
        status_data = status_json.get("data", {})
        if status_data.get("status") is True:
            total_sign = status_data.get("total_sign")
            total_get_traffic = status_data.get("total_get_traffic")
            last_sign = status_data.get("last_sign")

            msg = f"今日已签到，无需重复操作。累计签到 {total_sign} 天，累计流量 {total_get_traffic} {cfg['traffic_unit']}"
            logger.info(
                "今日已签到，无需重复操作。total_sign=%s, total_get_traffic=%s, last_sign=%s",
                total_sign, total_get_traffic, last_sign
            )
            write_status(
                result="already_signed",
                message=msg,
                extra={
                    "api_base": api_base,
                    "user_id": user_id,
                    "total_sign": total_sign,
                    "total_get_traffic": total_get_traffic,
                    "last_sign": last_sign,
                }
            )
            notify_already_signed(msg, cfg)
            return True

    elif status_code == 401:
        raise RuntimeError(f"查询签到状态仍然 401: {status_json}")
    else:
        logger.warning("查询签到状态异常，继续尝试签到。HTTP %s, 响应: %s", status_code, status_json)

    sign_code, sign_json = post_sign(session, api_base, access_token, user_id)

    if sign_code == 401:
        logger.warning("签到返回 401，重新获取 token 后重试一次")
        access_token, user_id = get_access_token(session, api_base, app_id, refresh_token)
        sign_code, sign_json = post_sign(session, api_base, access_token, user_id)

    if sign_code == 200 and sign_json.get("status") == 200:
        sign_data = sign_json.get("data", {})
        get_traffic = sign_data.get("get_traffic")
        total_value = extract_total_value(sign_data)
        first_sign = sign_data.get("first_sign")

        msg = f"签到成功，获得 {get_traffic} {cfg['traffic_unit']}，累计值 {total_value} {cfg['traffic_unit']}"
        logger.info(
            "签到成功。get_traffic=%s, total_value=%s, first_sign=%s, 原始响应=%s",
            get_traffic, total_value, first_sign, sign_json
        )
        write_status(
            result="signed",
            message=msg,
            extra={
                "api_base": api_base,
                "user_id": user_id,
                "get_traffic": get_traffic,
                "total_value": total_value,
                "first_sign": first_sign,
            }
        )
        notify_success(msg, cfg)
        return True

    message = str(sign_json.get("message", ""))
    if "already signed" in message.lower():
        msg = "接口返回今日已签到，无需重复操作"
        logger.info("%s。原始响应=%s", msg, sign_json)
        write_status(
            result="already_signed",
            message=msg,
            extra={
                "api_base": api_base,
                "user_id": user_id,
                "response": sign_json,
            }
        )
        notify_already_signed(msg, cfg)
        return True

    raise RuntimeError(f"签到失败: HTTP {sign_code}, 响应: {sign_json}")


# =========================
# 测试提醒
# =========================
def run_test_notification(kind, cfg):
    setup_logging()

    if kind == "success":
        logger.info("手动测试成功提醒")
        notify_success(f"测试提醒：签到成功，获得 1.23 {cfg['traffic_unit']}", cfg)
        return

    logger.info("手动测试失败提醒")
    test_msg = "测试提醒：接口异常或网络失败，请查看日志"
    write_status(result="failed", message=test_msg, extra={"source": "manual_test"})
    notify_failure(test_msg, cfg)


# =========================
# 主程序
# =========================
def main():
    cfg = None
    try:
        cfg = load_config()
    except Exception:
        cfg = {
            "traffic_unit": DEFAULT_TRAFFIC_UNIT,
            "notify_on_success": True,
            "notify_on_already_signed": False,
            "notify_on_failure": True,
            "popup_right_margin": 20,
            "popup_top": 40,
            "popup_stack_gap": 10,
            "popup_success_width": 400,
            "popup_success_height": 100,
            "popup_error_width": 470,
            "popup_error_height": 130,
            "persistent_error_width": 620,
            "persistent_error_height": 340,
        }

    if "--popup-window" in sys.argv:
        try:
            idx = sys.argv.index("--popup-window")
            kind = sys.argv[idx + 1]
            encoded_title = sys.argv[idx + 2]
            encoded_message = sys.argv[idx + 3]
            encoded_cfg = sys.argv[idx + 4]
            title = base64.urlsafe_b64decode(encoded_title.encode("ascii")).decode("utf-8")
            message = base64.urlsafe_b64decode(encoded_message.encode("ascii")).decode("utf-8")
            cfg = json.loads(base64.urlsafe_b64decode(encoded_cfg.encode("ascii")).decode("utf-8"))
        except Exception:
            kind = "error"
            title = "LoCyanFrp 自动签到"
            message = "右上角提示启动失败：无法解析提示内容。"
        run_popup_notification_window(title, message, kind, cfg)
        return

    if "--error-window" in sys.argv:
        try:
            idx = sys.argv.index("--error-window")
            encoded_message = sys.argv[idx + 1]
            encoded_cfg = sys.argv[idx + 2]
            message = base64.urlsafe_b64decode(encoded_message.encode("ascii")).decode("utf-8")
            cfg = json.loads(base64.urlsafe_b64decode(encoded_cfg.encode("ascii")).decode("utf-8"))
        except Exception:
            message = "错误窗口启动失败：无法解析错误信息。"
        run_persistent_error_window(message, cfg)
        return

    if "--test-success" in sys.argv:
        run_test_notification("success", cfg)
        return

    if "--test-failure" in sys.argv:
        run_test_notification("failure", cfg)
        return

    setup_logging()
    log_runtime_info()

    lock = SingleInstanceLock(LOCK_PATH)
    if not lock.acquire():
        logger.warning("检测到已有实例在运行，本次退出。")
        return

    try:
        logger.info("开始执行自动签到任务")
        config = load_config()
        session = build_session()

        last_error = None
        for api_base in API_BASES:
            try:
                ok = try_sign_once(session, api_base, config["app_id"], config["refresh_token"], config)
                if ok:
                    logger.info("任务执行完成")
                    return
            except requests.RequestException as e:
                last_error = f"{api_base} 网络异常: {e}"
                logger.error(last_error)
                time.sleep(2)
            except Exception as e:
                last_error = f"{api_base} 执行异常: {e}"
                logger.error(last_error)
                time.sleep(2)

        final_msg = f"所有 API 均执行失败。最后错误: {last_error}"
        logger.error(final_msg)
        write_status(result="failed", message=final_msg, extra={"last_error": last_error})
        notify_failure(final_msg, config)

    except Exception as e:
        final_msg = f"程序异常终止: {e}"
        logger.error(final_msg)
        write_status(result="failed", message=final_msg, extra={"exception": str(e)})
        notify_failure(final_msg, cfg)

    finally:
        lock.release()


if __name__ == "__main__":
    main()
