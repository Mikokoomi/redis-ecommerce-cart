"""Tải ảnh tham khảo, kiểm tra và lưu WebP cục bộ; không ghi Redis."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

import httpx
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from backend.catalog_import import load_catalog, DEFAULT_INPUT

def download(p,override):
    pid=p["id"]
    record=override.get(pid,{})
    url=record.get("image_url",p["image_url"])
    source=record.get("source_page",p["image_source_page"])
    try:
        headers={"User-Agent":"Mozilla/5.0","Referer":source}
        with httpx.Client(follow_redirects=True,timeout=30,headers=headers) as c:
            r=c.get(url)
            r.raise_for_status()
            content_type=r.headers.get("content-type","").split(";")[0].lower()
            if not content_type.startswith("image/"):
                raise ValueError("Response không phải image.")
            if len(r.content)>25_000_000:
                raise ValueError("Ảnh quá lớn.")
            with Image.open(BytesIO(r.content)) as original:
                original.load()
                img=ImageOps.exif_transpose(original).convert("RGBA")
                original_size=img.size
                if img.width<300:
                    raise ValueError("Chiều rộng dưới 300px.")
                if record.get("crop"):
                    img=img.crop(tuple(record["crop"]))
                # Giữ đúng tỷ lệ và alpha, không phóng to hoặc vẽ ảnh thay thế.
                img.thumbnail((1000,1000),Image.Resampling.LANCZOS)
                output=ROOT/f"frontend/assets/images/products/{pid}.webp"
                output.parent.mkdir(parents=True,exist_ok=True)
                img.save(output,"WEBP",quality=88,method=6)
                with Image.open(output) as verified:
                    verified.load()
                    size=verified.size
        return pid,{"status":"ok","name":p["name"],"url":url,"resolved_url":str(r.url),
                    "source_page":source,"manufacturer_url":p["manufacturer_url"],
                    "content_type":content_type,"original_size":original_size,"size":size,"crop":record.get("crop"),
                    "bytes":output.stat().st_size,"sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
                    "local":f"/assets/images/products/{pid}.webp"}
    except Exception as e:
        return pid,{"status":"failed","url":url,"error_type":type(e).__name__,"message":str(e)[:220]}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,default=DEFAULT_INPUT)
    parser.add_argument("--only",nargs="*")
    args=parser.parse_args()
    payload=load_catalog(args.input)
    override_path=ROOT/"tools/product-image-overrides.json"
    overrides=json.loads(override_path.read_text(encoding="utf-8")) if override_path.exists() else {}
    manifest_path=ROOT/"docs/product-image-manifest.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    rows=[p for p in payload["products"] if not args.only or p["id"] in args.only]
    with ThreadPoolExecutor(max_workers=5) as pool:
        for pid,result in pool.map(lambda p:download(p,overrides),rows):
            print(pid,result["status"],result.get("original_size"),result.get("message",""))
            manifest[pid]=result
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print("SUCCESS",sum(v["status"]=="ok" for v in manifest.values()),"FAILED",sum(v["status"]!="ok" for v in manifest.values()))

if __name__=="__main__":
    main()

