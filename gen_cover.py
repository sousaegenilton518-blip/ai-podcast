from PIL import Image, ImageDraw, ImageFont
import os

src = r"C:\Users\鸢尾花\.openclaw\media\inbound\672a4ae3-6de8-4ff4-a59c-e492caf64c31.jpg"
out = r"C:\Users\鸢尾花\.openclaw\workspace\podcasts\cover.jpg"

size = 1400
orig = Image.open(src).convert("RGB")
orig = orig.resize((size, size), Image.LANCZOS)

draw = ImageDraw.Draw(orig)

# 用背景色覆盖原图下半部分的文字区域（取原图底部颜色）
# 原图底部是深紫色渐变，用矩形覆盖文字
draw.rectangle([(0, 1050), (size, size)], fill="#1a1040")

font_paths = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]
fp = next((p for p in font_paths if os.path.exists(p)), None)
f_title = ImageFont.truetype(fp, 170) if fp else ImageFont.load_default()
f_sub   = ImageFont.truetype(fp, 65)  if fp else ImageFont.load_default()

# 主标题
title = "AI前沿速递"
bbox = draw.textbbox((0,0), title, font=f_title)
tw = bbox[2]-bbox[0]
draw.text(((size-tw)//2+3, 1083), title, font=f_title, fill="#110033")
draw.text(((size-tw)//2, 1080), title, font=f_title, fill="#FFFFFF")

# 副标题
sub = "小龙虾 出品"
bbox2 = draw.textbbox((0,0), sub, font=f_sub)
sw = bbox2[2]-bbox2[0]
draw.text(((size-sw)//2, 1290), sub, font=f_sub, fill="#8888AA")

orig.save(out, "JPEG", quality=96)
print(out)
