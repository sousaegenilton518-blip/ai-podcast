#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日AI播客生成脚本
抓取 TechCrunch RSS -> Claude 翻译 -> edge-tts 合成 -> 上传阿里云OSS -> 更新 RSS
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import asyncio
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
import os
import json
import base64
from datetime import datetime
import oss2

RSS_URL = "https://techcrunch.com/category/artificial-intelligence/feed/"
OUTPUT_DIR = r"C:\Users\鸢尾花\.openclaw\workspace\podcasts"
VOICE = "zh-CN-XiaoxiaoNeural"
GITHUB_TOKEN = "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"
GITHUB_REPO = "sousaegenilton518-blip/ai-podcast"
PAGES_BASE = "https://sousaegenilton518-blip.github.io/ai-podcast"
CONFIG_PATH = r"C:\Users\鸢尾花\.openclaw\openclaw.json"

# 阿里云 OSS 配置
OSS_ACCESS_KEY_ID = "LTAI5tAYKB1DctDWz7HDvwz8"
OSS_ACCESS_KEY_SECRET = "f16817zW81IZAVQLdQztWFSOpqkkpp"
OSS_BUCKET = "longxia-podcast"
OSS_ENDPOINT = "https://oss-cn-hangzhou.aliyuncs.com"
OSS_BASE_URL = "https://longxia-podcast.oss-cn-hangzhou.aliyuncs.com"

def oss_upload(local_path, oss_path):
    """上传文件到阿里云 OSS"""
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET)
    bucket.put_object_from_file(oss_path, local_path)
    url = f"{OSS_BASE_URL}/{oss_path}"
    print(f"OSS上传成功: {url}")
    return url

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

def generate_cn_title(en_title, script):
    """用 Claude 从脚本内容提取一个有内容的中文标题"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    provider = config["models"]["providers"]["claude-proxy"]
    api_key = provider["apiKey"]
    base_url = provider["baseUrl"]
    prompt = f"""根据以下播客脚本，生成一个简洁有内容的中文标题（15字以内），要体现具体内容，不要用"今天是xx月xx日"这种格式。只输出标题本身，不要任何解释。

脚本前200字：
{script[:200]}"""
    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/v1/messages",
        data=payload,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["content"][0]["text"].strip()

def translate_to_chinese(title, desc, max_retries=3):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    provider = config["models"]["providers"]["claude-proxy"]
    api_key = provider["apiKey"]
    base_url = provider["baseUrl"]
    today = datetime.now().strftime("%Y年%m月%d日")
    prompt = f"""你是一个AI播客主播，名叫小龙虾。请把以下英文播客内容改写成一段流畅自然的中文播客脚本，时长约3分钟（500-550字）。

要求：
- 全程中文，不要出现任何英文单词（专有名词可以保留英文但要加中文解释）
- 口语化，像在跟朋友聊天，可以适当加入自己的评论和见解
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
        req = urllib.request.Request(api_url + "?ref=main", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            existing = json.loads(resp.read())
            sha = existing.get("sha")
    except:
        pass
    body = {"message": commit_msg, "content": content, "branch": "main"}
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
        length = ep.get('length', 0)
        # 根据文件大小估算时长（edge-tts 约24kbps）
        secs = int(length / (24 * 1024 / 8)) if length else 0
        duration = f"{secs//60}:{secs%60:02d}" if secs else "0:00"
        items_xml += f"""
    <item>
      <title>{ep['title']}</title>
      <description>{ep['desc']}</description>
      <enclosure url="{ep['audio_url']}" type="audio/mpeg" length="{length}"/>
      <pubDate>{ep['pub_date']}</pubDate>
      <guid>{ep['audio_url']}</guid>
      <itunes:duration>{duration}</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
    </item>"""
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>龙虾说AI</title>
    <description>每天3分钟，带你了解AI最新动态。由龙虾说AI主播每日更新。</description>
    <link>{PAGES_BASE}</link>
    <language>zh-cn</language>
    <itunes:author>龙虾说AI</itunes:author>
    <itunes:image href="{OSS_BASE_URL}/images/cover.png?v=2"/>
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

    print("上传音频到阿里云OSS...")
    audio_url = oss_upload(output_path, f"audio/{audio_filename}")

    print("更新 RSS...")
    episodes = load_episodes()
    # 用原始英文标题生成中文标题
    today_title = title[:30] if len(title) < 30 else title[:30]
    try:
        today_title = generate_cn_title(title, script)
    except:
        today_title = title

    episodes.insert(0, {
        "title": today_title,
        "desc": script[:200] + "...",
        "audio_url": audio_url,
        "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
    })
    episodes = episodes[:30]  # 保留最近30期
    save_episodes(episodes)
    rss_url = update_rss(episodes)
    rss_path = os.path.join(OUTPUT_DIR, "feed.xml")
    oss_upload(rss_path, "feed.xml")
    github_upload(rss_path, "feed.xml", "Update RSS feed")

    print(f"音频已保存: {output_path}")
    print(f"音频URL: {audio_url}")
    print(f"RSS URL: {rss_url}")
    return output_path, audio_url, rss_url

if __name__ == "__main__":
    path, audio_url, rss_url = main()
    print(f"\nRSS订阅地址（复制到小宇宙）:\n{rss_url}")
