#!/usr/bin/env python3
"""生成小纪念应用图标"""
import os

# 创建 SVG 图标
svg_icon = '''<svg viewBox="0 0 192 192" xmlns="http://www.w3.org/2000/svg">
  <!-- 背景 -->
  <rect width="192" height="192" fill="#FDF5F7" rx="45"/>

  <!-- 装饰圆圈 -->
  <circle cx="96" cy="96" r="85" fill="none" stroke="#C8607A" stroke-width="2" opacity="0.3"/>

  <!-- 蝴蝶结 -->
  <!-- 左翅膀 -->
  <path d="M 60 96 Q 50 80 40 70 Q 45 65 52 72 Q 62 82 70 96 Z" fill="#C8607A" opacity="0.9"/>
  <!-- 右翅膀 -->
  <path d="M 132 96 Q 142 80 152 70 Q 147 65 140 72 Q 130 82 122 96 Z" fill="#C8607A" opacity="0.9"/>

  <!-- 左尾巴 -->
  <path d="M 65 100 Q 55 115 45 130 Q 50 135 57 130 Q 67 115 75 100 Z" fill="#C8607A" opacity="0.85"/>
  <!-- 右尾巴 -->
  <path d="M 127 100 Q 137 115 147 130 Q 142 135 135 130 Q 125 115 117 100 Z" fill="#C8607A" opacity="0.85"/>

  <!-- 中心结 -->
  <circle cx="96" cy="96" r="12" fill="#E8909A" opacity="0.95"/>
  <circle cx="96" cy="96" r="7" fill="#C8607A"/>
  <circle cx="96" cy="96" r="3" fill="#E8909A" opacity="0.6"/>

  <!-- 装饰点 -->
  <circle cx="96" cy="50" r="3" fill="#C8607A" opacity="0.5"/>
  <circle cx="140" cy="140" r="2.5" fill="#C8607A" opacity="0.4"/>
  <circle cx="52" cy="140" r="2.5" fill="#C8607A" opacity="0.4"/>
</svg>'''

# 保存 SVG
with open('/tmp/icon.svg', 'w') as f:
    f.write(svg_icon)

print("SVG 图标已生成")
print("请使用在线工具转换为 PNG:")
print("1. 访问 https://convertio.co/svg-png/")
print("2. 上传 /tmp/icon.svg")
print("3. 下载 192x192 和 512x512 版本")
print("4. 保存为 icon-192.png 和 icon-512.png")
