"""Tạo bảng ảnh để kiểm tra trực quan nội bộ."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root=Path(__file__).resolve().parent.parent
sheet=Image.new("RGB",(1250,1080),"white")
draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",14)
for i in range(20):
    pid=f"SP{i+1:03}"
    path=root/f"frontend/assets/images/products/{pid}.webp"
    x,y=(i%5)*250,(i//5)*270
    if path.exists():
        with Image.open(path) as original:
            img=original.convert("RGBA")
            img.thumbnail((235,230))
            sheet.paste(img,(x+(250-img.width)//2,y),img)
    draw.text((x+10,y+235),pid,fill="black",font=font)
(root/"work").mkdir(exist_ok=True)
sheet.save(root/"work/image-contact-sheet.jpg")
