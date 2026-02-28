#!/usr/bin/env python3
"""
微信小程序订阅消息推送系统
功能：
  - 管理订阅用户列表
  - 获取 access_token
  - 每日推送 AI 资讯订阅消息
"""

import json
import urllib.request
import urllib.parse
import sys
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "miniprogram_config.json")
USERS_FILE = os.path.join(BASE_DIR, "miniprogram_users.json")
TOKEN_FILE = os.path.join(BASE_DIR, "miniprogram_token.json")


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def get_access_token(appid, appsecret):
    """获取微信 access_token，带缓存"""
    # 检查缓存
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            cache = json.load(f)
        if cache.get("expires_at", 0) > datetime.now().timestamp() + 300:
            return cache["access_token"]

    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        result = json.loads(resp.read())

    if "access_token" not in result:
        raise Exception(f"获取 token 失败: {result}")

    # 缓存 token
    cache = {
        "access_token": result["access_token"],
        "expires_at": datetime.now().timestamp() + result["expires_in"]
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(cache, f)

    return result["access_token"]


def load_users():
    """加载订阅用户列表"""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def add_user(openid, template_id):
    """添加订阅用户"""
    users = load_users()
    for u in users:
        if u["openid"] == openid:
            u["template_id"] = template_id
            u["subscribed_at"] = datetime.now().isoformat()
            break
    else:
        users.append({
            "openid": openid,
            "template_id": template_id,
            "subscribed_at": datetime.now().isoformat()
        })
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    print(f"用户 {openid} 已添加")


def send_subscribe_message(access_token, openid, template_id, news_title, date_str):
    """发送订阅消息"""
    url = "https://api.weixin.qq.com/cgi-bin/message/subscribe/send"
    payload = {
        "touser": openid,
        "template_id": template_id,
        "miniprogram_state": "formal",
        "lang": "zh_CN",
        "data": {
            "thing1": {"value": news_title[:20]},
            "date2": {"value": date_str},
            "thing3": {"value": "爪爪机器人"},
            "thing4": {"value": "AIbase/Anthropic"}
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{url}?access_token={access_token}",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def push_to_all(news_title, news_summary):
    """推送给所有订阅用户"""
    config = load_config()
    users = load_users()

    if not users:
        print("暂无订阅用户")
        return

    token = get_access_token(config["appid"], config["appsecret"])
    date_str = datetime.now().strftime("%Y年%m月%d日")
    success, fail = 0, 0

    for user in users:
        result = send_subscribe_message(
            token,
            user["openid"],
            user["template_id"],
            news_title,
            date_str
        )
        if result.get("errcode") == 0:
            success += 1
        else:
            print(f"推送失败 {user['openid']}: {result}")
            fail += 1

    print(f"推送完成：成功 {success}，失败 {fail}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")

    # 添加用户
    p_add = subparsers.add_parser("add-user")
    p_add.add_argument("--openid", required=True)
    p_add.add_argument("--template-id", required=True)

    # 推送
    p_push = subparsers.add_parser("push")
    p_push.add_argument("--title", required=True)

    # 测试 token
    p_token = subparsers.add_parser("token")

    args = parser.parse_args()

    if args.cmd == "add-user":
        add_user(args.openid, args.template_id)
    elif args.cmd == "push":
        push_to_all(args.title)
    elif args.cmd == "token":
        config = load_config()
        token = get_access_token(config["appid"], config["appsecret"])
        print(f"access_token: {token[:20]}...")
    else:
        parser.print_help()
