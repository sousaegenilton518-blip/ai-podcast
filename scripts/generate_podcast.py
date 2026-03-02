#!/usr/bin/env python3
"""GitHub Actions 自动播客生成脚本"""
import asyncio
import urllib.request
import xml.etree.ElementTree as ET
import re
import os
import json
from datetime import datetime

RSS_URL = "https://techcrunch.com/feed/"
VOICE = "zh-CN-XiaoxiaoNeural"
PAGES_BASE = "https://sousaegenilton518-blip.github.io/ai-podcast"

def fetch_latest_news():
    with urllib.request.urlopen(RSS_URL, timeout=15) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    item = root.find(".//item")
    title = item.findtext("title", "")
    desc_raw = item.findtext("description", "")
    desc = re.sub(r"<[^>]+>", "", desc_raw).strip()
    return title, desc[:1500]

def translate_to_chinese(title, desc):
    import anthropic
    client = anthropic.Anthropic()
    today = datetime.now().strftime("%Y年%m月%d日")
    prompt = f"""你是一个AI播客主播，名叫小龙虾。请将以下英文新闻改写成一段自然流畅的中文播客脚本，时长约3分钟（600-700字）。

要求：
- 全程中文，不要保留任何英文单词，专有名词可以保留英文但要加中文解释
- 口语化，适合朗读播放
- 开头："大家好，我是小龙虾，欢迎收听今天的AI前沿速递。今天是{today}。"
- 结尾："以上就是今天的AI前沿速递。我是小龙虾，同一时间，我们江湖再见拜拜。"

新闻标题：{title}

新闻摘要：
{desc}"""
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

async def generate_audio(script, output_path):
    import edge_tts
    communicate = edge_tts.Communicate(script, VOICE)
    await communicate.save(output_path)

def extract_title(script):
    lines = script.split('。')
    for line in lines:
        if '今天要' in line or '分享' in line:
            content = line.split('今天要')[-1] if '今天要' in line else line
            content = content.replace('跟大家分享', '').replace('的是', '').strip()
            if len(content) > 10:
                return f"AI前沿速递：{content[:30]}"
    return f"AI前沿速递：{datetime.now().strftime('%Y年%m月%d日')}"

def update_feed(new_title, script, audio_filename):
    feed_path = "feed.xml"
    with open(feed_path, "r", encoding="utf-8") as f:
        content = f.read()
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
    audio_url = f"{PAGES_BASE}/audio/{audio_filename}"
    new_item = f'''    <item>
      <title>{new_title}</title>
      <description>{script[:200]}...</description>
      <enclosure url="{audio_url}" type="audio/mpeg" length="0"/>
      <pubDate>{pub_date}</pubDate>
      <guid>{audio_url}</guid>
    </item>
    <item>'''
    content = content.replace("    <item>", new_item, 1)
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    today_str = datetime.now().strftime("%Y-%m-%d")
    audio_filename = f"podcast_{today_str}.mp3"
    audio_path = f"audio/{audio_filename}"
    os.makedirs("audio", exist_ok=True)
    print("抓取最新新闻...")
    title, desc = fetch_latest_news()
    print(f"标题: {title}")
    print("生成中文脚本...")
    script = translate_to_chinese(title, desc)
    print("合成音频...")
    asyncio.run(generate_audio(script, audio_path))
    print("更新RSS...")
    new_title = extract_title(script)
    update_feed(new_title, script, audio_filename)
    print(f"完成！音频: {audio_path}")

if __name__ == "__main__":
    main()
