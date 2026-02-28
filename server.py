#!/usr/bin/env python3
"""
AI 每日资讯 - 小程序后端服务
框架：FastAPI + Uvicorn
部署：uvicorn server:app --host 0.0.0.0 --port 8080
"""

import json
import urllib.request
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "miniprogram_config.json")
USERS_FILE = os.path.join(BASE_DIR, "miniprogram_users.json")
TOKEN_FILE = os.path.join(BASE_DIR, "miniprogram_token.json")

app = FastAPI(title="AI每日资讯后端", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 工具函数 ----------

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def get_access_token():
    config = load_config()
    # 检查缓存
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            cache = json.load(f)
        if cache.get("expires_at", 0) > datetime.now().timestamp() + 300:
            return cache["access_token"]
    # 重新获取
    url = (
        f"https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential"
        f"&appid={config['appid']}&secret={config['appsecret']}"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        result = json.loads(resp.read())
    if "access_token" not in result:
        raise Exception(f"获取 token 失败: {result}")
    cache = {
        "access_token": result["access_token"],
        "expires_at": datetime.now().timestamp() + result["expires_in"]
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(cache, f)
    return result["access_token"]

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def code2session(appid, appsecret, code):
    url = (
        f"https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={appid}&secret={appsecret}"
        f"&js_code={code}&grant_type=authorization_code"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


# ---------- 接口 ----------

class SubscribeRequest(BaseModel):
    code: str
    template_id: str

class PushRequest(BaseModel):
    title: str
    secret: str  # 简单鉴权，防止外部乱调


@app.get("/")
def health():
    return {"status": "ok", "service": "AI每日资讯后端"}


@app.post("/subscribe")
def subscribe(req: SubscribeRequest):
    """小程序用户订阅"""
    config = load_config()
    result = code2session(config["appid"], config["appsecret"], req.code)
    if "openid" not in result:
        raise HTTPException(status_code=400, detail=f"code 换取 openid 失败: {result}")

    openid = result["openid"]
    users = load_users()
    if not any(u["openid"] == openid for u in users):
        users.append({
            "openid": openid,
            "template_id": req.template_id,
            "subscribed_at": datetime.now().isoformat()
        })
        save_users(users)

    return {"ok": True, "openid": openid[:8] + "****"}


@app.post("/push")
def push(req: PushRequest):
    """推送订阅消息给所有用户（由定时任务调用）"""
    config = load_config()
    # 简单鉴权
    if req.secret != config.get("push_secret", "ai-news-2026"):
        raise HTTPException(status_code=403, detail="鉴权失败")

    users = load_users()
    if not users:
        return {"ok": True, "sent": 0, "message": "暂无订阅用户"}

    token = get_access_token()
    date_str = datetime.now().strftime("%Y年%m月%d日")
    success, fail = 0, 0

    for user in users:
        payload = {
            "touser": user["openid"],
            "template_id": user["template_id"],
            "miniprogram_state": "formal",
            "lang": "zh_CN",
            "data": {
                "thing1": {"value": req.title[:20]},
                "date2": {"value": date_str},
                "thing3": {"value": "爪爪机器人"},
                "thing4": {"value": "AIbase/Anthropic"}
            }
        }
        data = json.dumps(payload).encode("utf-8")
        push_req = urllib.request.Request(
            f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={token}",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(push_req, timeout=10) as resp:
                r = json.loads(resp.read())
                if r.get("errcode") == 0:
                    success += 1
                else:
                    fail += 1
        except Exception:
            fail += 1

    return {"ok": True, "sent": success, "failed": fail}


@app.get("/users/count")
def user_count():
    """查看订阅用户数"""
    return {"count": len(load_users())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=False)
