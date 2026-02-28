#!/usr/bin/env python3
"""
每日AI播客生成脚本
抓取 Lex Fridman RSS -> Claude 翻译 -> edge-tts 合成 -> 上传 GitHub Pages -> 更新 RSS
"""
import asyncio
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
import os
import json
import base64
from datetime import datetime

RSS_URL = "https://techcrunch.com/feed/"  # 改用TechCrunch作为新闻源
OUTPUT_DIR = r"C:\Users\鸢尾花\.openclaw\workspace\podcasts"
VOICE = "zh-CN-XiaoxiaoNeural"
GITHUB_TOKEN = "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"
GITHUB_REPO = "sousaegenilton518-blip/ai-podcast"
PAGES_BASE = "https://sousaegenilton518-blip.github.io/ai-podcast"
CONFIG_PATH = r"C:\Users\鸢尾花\.openclaw\openclaw.json"

def fetch_latest_episode():
    with urllib.request.urlopen(RSS_URL, timeout=15) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    item = root.find(".//item")
    title = item.findtext("title", "")
    desc_raw = item.findtext("description", "")
    desc = re.sub(r"<[^>]+>", "", desc_raw).strip()
    pub_date = item.findtext("pubDate", "")
    return title, desc[:1500], pub_date

def translate_to_chinese(title, desc, max_retries=3):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    provider = config["models"]["providers"]["claude-proxy"]
    api_key = provider["apiKey"]
    base_url = provider["baseUrl"]
    today = datetime.now().strftime("%Y年%m月%d日")
    prompt = f"""你是一个AI播客主播，名叫小龙虾。请把以下英文播客内容改写成一段流畅自然的中文播客脚本，时长约3分钟（600-700字）。

要求：
- 全程中文，不要出现任何英文单词（专有名词可以保留英文但要加中文解释）
- 口语化，像在跟朋友聊天
- 开头："大家好，我是小龙虾，欢迎收听今天的AI前沿速递。今天是{today}。"
- 结尾："以上就是今天的AI前沿速递。我是小龙虾，明天同一时间，我们继续。拜拜。"

播客标题：{title}

内容摘要：
{desc}"""
    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    return result["content"][0]["text"]

async def generate_audio(script, output_path):
    import edge_tts
    communicate = edge_tts.Communicate(script, VOICE)
    await communicate.save(output_path)

def github_upload(file_path, repo_path, commit_msg):
    """上传文件到 GitHub 仓库"""
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{repo_path}"
    # 检查文件是否已存在（获取 sha）
    sha = None
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            existing = json.loads(resp.read())
            sha = existing.get("sha")
    except:
        pass
    body = {"message": commit_msg, "content": content}
    if sha:
        body["sha"] = sha
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(api_url, data=payload, headers=headers, method="PUT")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def update_rss(episodes):
    """生成并上传 RSS feed"""
    items_xml = ""
    for ep in episodes:
        items_xml += f"""
    <item>
      <title>{ep['title']}</title>
      <description>{ep['desc']}</description>
      <enclosure url="{ep['audio_url']}" type="audio/mpeg" length="0"/>
      <pubDate>{ep['pub_date']}</pubDate>
      <guid>{ep['audio_url']}</guid>
    </item>"""
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>AI前沿速递</title>
    <description>每天3分钟，带你了解AI最新动态。由小龙虾AI主播每日更新。</description>
    <link>{PAGES_BASE}</link>
    <language>zh-cn</language>
    <itunes:author>小龙虾</itunes:author>
    <itunes:category text="Technology"/>
    <itunes:explicit>false</itunes:explicit>{items_xml}
  </channel>
</rss>"""
    rss_path = os.path.join(OUTPUT_DIR, "feed.xml")
    with open(rss_path, "w", encoding="utf-8") as f:
        f.write(rss)
    github_upload(rss_path, "feed.xml", "Update RSS feed")
    return f"{PAGES_BASE}/feed.xml"

def load_episodes():
    ep_file = os.path.join(OUTPUT_DIR, "episodes.json")
    if os.path.exists(ep_file):
        with open(ep_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_episodes(episodes):
    ep_file = os.path.join(OUTPUT_DIR, "episodes.json")
    with open(ep_file, "w", encoding="utf-8") as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    audio_filename = f"podcast_{today_str}.mp3"
    output_path = os.path.join(OUTPUT_DIR, audio_filename)

    print("抓取最新播客...")
    title, desc, pub_date = fetch_latest_episode()
    print(f"标题: {title}")

    print("翻译内容为中文...")
    script = translate_to_chinese(title, desc)

    print("合成音频...")
    asyncio.run(generate_audio(script, output_path))

    print("上传音频到 GitHub...")
    github_upload(output_path, f"audio/{audio_filename}", f"Add podcast {today_str}")
    audio_url = f"{PAGES_BASE}/audio/{audio_filename}"

    print("更新 RSS...")
    episodes = load_episodes()
    # 从翻译后的内容中提取实际主题作为标题
    content_start = script.split('。')[1].strip() if '。' in script else script
    today_title = f"AI前沿速递：{content_start}"
    episodes.insert(0, {
        "title": today_title,
        "desc": script[:200] + "...",
        "audio_url": audio_url,
        "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
    })
    episodes = episodes[:30]  # 保留最近30期
    save_episodes(episodes)
    rss_url = update_rss(episodes)

    print(f"音频已保存: {output_path}")
    print(f"音频URL: {audio_url}")
    print(f"RSS URL: {rss_url}")
    return output_path, audio_url, rss_url

if __name__ == "__main__":
    path, audio_url, rss_url = main()
    print(f"\nRSS订阅地址（复制到小宇宙）:\n{rss_url}")
