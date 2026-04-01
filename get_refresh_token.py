import json
import os
import requests

API_BASES = [
    "https://api.locyanfrp.cn/v3",
    "https://backup.api.locyanfrp.cn/v3",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
EXAMPLE_PATH = os.path.join(BASE_DIR, "config.example.json")


def load_or_create_config():
    if os.path.exists(CONFIG_PATH):
        path = CONFIG_PATH
    else:
        path = EXAMPLE_PATH

    if not os.path.exists(path):
        raise FileNotFoundError("找不到 config.json 或 config.example.json")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def exchange_code_for_refresh_token(code: str):
    last_error = None

    for api_base in API_BASES:
        url = f"{api_base}/auth/oauth/refresh-token"
        try:
            resp = requests.post(url, data={"code": code}, timeout=15)
            data = resp.json()

            if resp.status_code == 200 and data.get("status") == 200:
                refresh_token = data["data"]["refresh_token"]
                return {
                    "api_base": api_base,
                    "refresh_token": refresh_token,
                    "raw": data,
                }

            last_error = f"{api_base} 返回异常: HTTP {resp.status_code}, 响应: {data}"
        except Exception as e:
            last_error = f"{api_base} 请求失败: {e}"

    raise RuntimeError(last_error or "未知错误")


def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def main():
    print("=== LoCyanFrp 初始化：兑换 refresh_token ===")

    config = load_or_create_config()
    app_id = str(config.get("app_id", "")).strip()
    if not app_id:
        app_id = input("请输入 app_id：").strip()
        config["app_id"] = app_id

    code = input("请粘贴刚拿到的一次性 code：").strip()
    if not code:
        print("未输入 code，已退出。")
        return

    result = exchange_code_for_refresh_token(code)
    refresh_token = result["refresh_token"]

    config["refresh_token"] = refresh_token
    save_config(config)

    print("\n✅ 已成功获取 refresh_token 并写入 config.json")
    print(f"使用的 API: {result['api_base']}")
    print(f"配置文件路径: {CONFIG_PATH}")
    print(f"refresh_token 前8位: {refresh_token[:8]}...")
    print("请不要把完整 refresh_token 提交到 GitHub。")


if __name__ == "__main__":
    main()
