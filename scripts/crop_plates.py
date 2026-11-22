#!/usr/bin/env python3
"""Extract the original engraved IMAGE from each original 1768 plate scan.

Never create, inpaint, denoise, extend or fabricate historical artwork.
The full unmodified scan remains in public/art and is linked from provenance.
This is a separate, explicitly cropped reproduction for readers.
"""
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
import json

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"public/art"
OUT=ROOT/"public/engravings"
THUMBS=OUT/"thumb"
SAMPLE_IDS=[1,2,3,4,6,15,26,32,43,52,53,60,70,84,90,100,104]

# Coordinates deliberately cut away all outer book leaves, archival watermarks,
# captions and the page-number strip. Composition stays uncropped inside engraving.
# These are within the engraved *picture* rather than the title cartouche.
BASE_CROP=(0.108,0.103,0.837,0.724)
# One-off overrides can be introduced only after visual comparison with full scans.
OVERRIDES={1:(0.108,0.103,0.837,0.713),100:(0.108,0.103,0.837,0.708)}

def crop_image(image, number):
    im=ImageOps.exif_transpose(image).convert("RGB")
    width,height=im.size
    left,top,right,bottom=OVERRIDES.get(number,BASE_CROP)
    bounds=(round(width*left),round(height*top),round(width*right),round(height*bottom))
    if bounds[2]-bounds[0]<100 or bounds[3]-bounds[1]<180:
        raise ValueError(f"Invalid crop for engraving {number}: {bounds}")
    return im.crop(bounds), bounds

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    THUMBS.mkdir(exist_ok=True,parents=True)
    info={}
    for number in range(1,105):
        source=SOURCE/f"{number:03d}.webp"
        with Image.open(source) as image:
            cropped,bounds=crop_image(image,number)
            cropped.save(OUT/f"{number:03d}.webp",format="WEBP",quality=89,method=5)
            reduced=cropped.copy()
            reduced.thumbnail((540,900),Image.Resampling.LANCZOS)
            reduced.save(THUMBS/f"{number:03d}.webp",format="WEBP",quality=83,method=5)
            info[str(number)]={"bounds_px":bounds,"source_size":image.size,"crop_size":cropped.size}
    # audit mosaic uses only the historic originals. NOT a site asset.
    panels=[]
    for number in SAMPLE_IDS:
        with Image.open(OUT/f"{number:03d}.webp") as im:
            pane=Image.new("RGB",(230,356),"#e9e2d5")
            c=im.copy()
            c.thumbnail((205,314),Image.Resampling.LANCZOS)
            pane.paste(c,((230-c.width)//2,9))
            dr=ImageDraw.Draw(pane)
            dr.text((12,335),f"{number:03d}  |  engraved image crop",fill="#282b29")
            panels.append(pane)
    columns=5
    rows=(len(panels)+columns-1)//columns
    board=Image.new("RGB",(columns*230,rows*356),"#e9e2d5")
    for i,pane in enumerate(panels):
        board.paste(pane,((i%columns)*230,(i//columns)*356))
    (ROOT/"qa").mkdir(exist_ok=True)
    board.save(ROOT/"qa/crop-contact.jpg",quality=87,optimize=True)
    (ROOT/"public/data/crop-provenance.json").write_text(json.dumps({
      "source":"Giessen 1768, Universitätsbibliothek Heidelberg; each original full scan retained under public/art/",
      "technique":"lossless spatial selection with WebP delivery; no pixels invented",
      "base_normalized_bbox":BASE_CROP,
      "plates":info
    },ensure_ascii=False,indent=2))
    assert len(list(OUT.glob("*.webp")))==104
    assert len(list(THUMBS.glob("*.webp")))==104
    print("PASS: 104 individually cropped ORIGINAL engravings, 104 thumbnails, 104 source provenance records")

if __name__=="__main__":
    main()
