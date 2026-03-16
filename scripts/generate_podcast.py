#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub Actions 自动播客生成脚本（从环境变量读取配置）"""
import asyncio
import urllib.request
import xml.etree.ElementTree as ET
import re
import os
import json
import base64
from datetime import datetime

RSS_URL = "https://techcrunch.com/feed/"
VOICE = "zh-CN-XiaoxiaoNeural"
GITHUB_REPO = "sousaegenilton518-blip/ai-podcast"
PAGES_BASE = "https://sousaegenilton518-blip.github.io/ai-podcast"

CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
CLAUDE_BASE_URL = os.environ.get("CLAUDE_BASE_URL", "https://api.anthropic.com")
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]


def fetch_latest_episode():
    # 抓取多条，找第一条含 AI 关键词的
    with urllib.request.urlopen(RSS_URL, timeout=15) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    ai_keywords = ["AI", "artificial intelligence", "machine learning", "OpenAI",
                   "Anthropic", "Google", "Meta", "model", "LLM", "robot", "automation"]
    for item in root.findall(".//item"):
        title = item.findtext("title", "")
        desc_raw = item.findtext("description", "")
        text = (title + desc_raw).lower()
        if any(k.lower() in text for k in ai_keywords):
            desc = re.sub(r"<[^>]+>", "", desc_raw).strip()
            return title, desc[:1500]
    # 没找到就用第一条
    item = root.find(".//item")
    title = item.findtext("title", "")
    desc = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
    return title, desc[:1500]


def translate_to_chinese(title, desc):
    today = datetime.now().strftime("%Y年%m月%d日")
    prompt = f"""你是一个AI播客主播，名叫小龙虾。请把以下英文内容改写成流畅自然的中文播客脚本，时长约3分钟（500-550字）。

要求：
- 全程中文，专有名词保留英文但加中文解释
- 口语化，像在跟朋友聊天
- 开头："大家好，我是小龙虾，欢迎收听今天的AI前沿速递。今天是{today}。"
- 结尾："以上就是今天的AI前沿速递。我是小龙虾，明天同一时间，我们继续。拜拜。"

标题：{title}
摘要：{desc}"""
    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{CLAUDE_BASE_URL}/v1/messages",
        data=payload,
        headers={
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["content"][0]["text"]


def generate_cn_title(script):
    prompt = f"根据以下播客脚本，生成一个简洁有内容的中文标题（15字以内），只输出标题本身。\n\n{script[:200]}"
    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{CLAUDE_BASE_URL}/v1/messages",
        data=payload,
        headers={
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["content"][0]["text"].strip()


async def generate_audio(script, output_path):
    import edge_tts
    communicate = edge_tts.Communicate(script, VOICE)
    await communicate.save(output_path)


def github_upload(file_path, repo_path, commit_msg):
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "podcast-bot"
    }
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{repo_path}"
    sha = None
    try:
        req = urllib.request.Request(api_url + "?ref=main", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            sha = json.loads(resp.read()).get("sha")
    except Exception:
        pass
    body = {"message": commit_msg, "content": content, "branch": "main"}
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(
        api_url, data=json.dumps(body).encode(), headers=headers, method="PUT"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def update_episodes_json(episodes):
    ep_path = "episodes.json"
    with open(ep_path, "w", encoding="utf-8") as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)
    github_upload(ep_path, "episodes.json", "Update episodes.json")


def update_rss(episodes):
    items_xml = ""
    for ep in episodes:
        items_xml += f"""
    <item>
      <title>{ep['title']}</title>
      <description><![CDATA[{ep['desc']}]]></description>
      <enclosure url="{ep['audio_url']}" type="audio/mpeg" length="0"/>
      <pubDate>{ep['pub_date']}</pubDate>
      <guid>{ep['audio_url']}</guid>
    </item>"""
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>龙虾说AI</title>
    <description>每天3分钟，带你了解AI最新动态。</description>
    <link>{PAGES_BASE}</link>
    <language>zh-cn</language>
    <itunes:author>龙虾说AI</itunes:author>
    <itunes:category text="Technology"/>
    <itunes:explicit>false</itunes:explicit>{items_xml}
  </channel>
</rss>"""
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss)
    github_upload("feed.xml", "feed.xml", "Update RSS feed")


def main():
    today_str = datetime.now().strftime("%Y-%m-%d")
    audio_filename = f"podcast_{today_str}.mp3"
    os.makedirs("audio", exist_ok=True)

    print("抓取新闻...")
    title, desc = fetch_latest_episode()
    print(f"标题: {title}")

    print("生成脚本...")
    script = translate_to_chinese(title, desc)

    print("合成音频...")
    asyncio.run(generate_audio(script, f"audio/{audio_filename}"))

    print("上传音频到 GitHub...")
    audio_url = f"{PAGES_BASE}/audio/{audio_filename}"
    github_upload(f"audio/{audio_filename}", f"audio/{audio_filename}",
                  f"Add podcast {today_str}")

    print("更新 episodes.json 和 RSS...")
    ep_title = generate_cn_title(script)
    episodes = []
    if os.path.exists("episodes.json"):
        with open("episodes.json", encoding="utf-8") as f:
            episodes = json.load(f)
    episodes.insert(0, {
        "title": ep_title,
        "desc": script[:200] + "...",
        "audio_url": audio_url,
        "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
    })
    episodes = episodes[:30]
    update_episodes_json(episodes)
    update_rss(episodes)

    print(f"完成！{audio_url}")


if __name__ == "__main__":
    main()

