#!/usr/bin/env python3
"""生成小纪念应用的爱心图标"""
from PIL import Image, ImageDraw
import math

def create_heart_icon(size, scale=12.6):
    """生成爱心图标"""
    # 创建图像
    img = Image.new('RGBA', (size, size), (253, 245, 247, 255))
    draw = ImageDraw.Draw(img)

    # 中心点
    cx, cy = size / 2, size / 2

    # 绘制爱心
    points = []
    for t in range(0, 628):  # 0 to 2π
        angle = t / 100.0
        x = 16 * math.sin(angle) ** 3
        y = 13 * math.cos(angle) - 5 * math.cos(2*angle) - 2 * math.cos(3*angle) - math.cos(4*angle)

        px = cx + x * scale * (size / 192)
        py = cy - y * scale * (size / 192)
        points.append((px, py))

    # 填充爱心
    draw.polygon(points, fill=(200, 96, 122, 255))

    # 保存图像
    img.save(f'icon-{size}.png')
    print(f"已生成 icon-{size}.png")

# 生成两个尺寸的图标
create_heart_icon(192, scale=12.6)
create_heart_icon(512, scale=12.6)
print("爱心图标生成完成！")
