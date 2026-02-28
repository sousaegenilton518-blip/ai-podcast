#!/usr/bin/env python3
"""
微信小程序后端服务
接口：POST /subscribe - 接收 code，换取 openid，保存订阅
运行：python server.py
"""

import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "miniprogram_config.json")
USERS_FILE = os.path.join(os.environ.get("DATA_DIR", BASE_DIR), "miniprogram_users.json")

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def code2session(appid, appsecret, code):
    url = f"https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={appsecret}&js_code={code}&grant_type=authorization_code"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())

def save_user(openid, template_id):
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    for u in users:
        if u["openid"] == openid:
            return  # 已存在
    users.append({"openid": openid, "template_id": template_id})
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    print(f"新用户订阅: {openid}")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # 静默日志

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path != "/subscribe":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        code = body.get("code")
        template_id = body.get("template_id")

        config = load_config()
        result = code2session(config["appid"], config["appsecret"], code)

        if "openid" not in result:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": result}).encode())
            return

        save_user(result["openid"], template_id)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"后端服务启动，监听端口 {port}")
    print("等待用户订阅...")
    server.serve_forever()
