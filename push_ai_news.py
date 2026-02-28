#!/usr/bin/env python3
"""
AI 每日资讯推送脚本
支持：企业微信群机器人 webhook
用法：python push_ai_news.py --webhook <URL>
"""

import argparse
import json
import urllib.request
import urllib.error
import sys
from datetime import datetime

def send_to_wecom(webhook_url: str, content: str) -> bool:
    """发送文本消息到企业微信群机器人"""
    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("errcode") == 0:
                print("发送成功")
                return True
            else:
                print(f"发送失败: {result}")
                return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False


def send_image_to_wecom(webhook_url: str, image_path: str) -> bool:
    """发送图片到企业微信群机器人（base64）"""
    import base64
    import hashlib

    with open(image_path, "rb") as f:
        img_data = f.read()

    img_base64 = base64.b64encode(img_data).decode("utf-8")
    img_md5 = hashlib.md5(img_data).hexdigest()

    payload = {
        "msgtype": "image",
        "image": {
            "base64": img_base64,
            "md5": img_md5
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get("errcode") == 0:
                print("图片发送成功")
                return True
            else:
                print(f"图片发送失败: {result}")
                return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 资讯推送到企业微信群")
    parser.add_argument("--webhook", required=True, help="企业微信群机器人 webhook URL")
    parser.add_argument("--image", help="图片路径（可选，发图片模式）")
    parser.add_argument("--text", help="文本内容（可选，发文字模式）")
    args = parser.parse_args()

    if args.image:
        success = send_image_to_wecom(args.webhook, args.image)
    elif args.text:
        success = send_to_wecom(args.webhook, args.text)
    else:
        print("请指定 --image 或 --text")
        sys.exit(1)

    sys.exit(0 if success else 1)
