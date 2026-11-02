#!/usr/bin/env python3
"""Compare glyph/shape ink against an independently rendered background frame.

Adapted from the supplied Chromium design check, using Pillow only. Input images
must be unprocessed captures of the same background and size. No font is bundled.
"""
import argparse
from PIL import Image, ImageChops


def check(shot, background, scale=1, edge=72, login_top=None, error_shown=False, clock_only=False):
    if shot.size != background.size:
        raise ValueError(f'Size mismatch: {shot.size} vs {background.size}')
    top=login_top if login_top is not None else max(220, round(.451*shot.height/scale))
    bands=[('clock',66,132),('date',148,174)]
    if not clock_only:
        bands += [('avatar',top+4,top+44),('field border',top+70,top+104)]
        if error_shown: bands.append(('error message',top+115,top+134))
        row=top+(153.5 if error_shown else 127.5)
        bands.append(('first bottom label',row-3,row+16))
    difference=ImageChops.difference(shot.convert('RGB'),background.convert('RGB'))
    results=[]
    x0,x1=round((edge-20)*scale),round((edge+40)*scale)
    for name,y0,y1 in bands:
        found=None
        for x in range(x0,x1):
            if any(sum(difference.getpixel((x,y)))>60 for y in range(round(y0*scale),round(y1*scale))):
                found=x/scale;break
        results.append(dict(element=name,leftmost_ink=found,target=edge,passed=found is not None and abs(found-edge)<=1.5))
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('shot');parser.add_argument('background')
    parser.add_argument('--scale',type=float,default=1)
    parser.add_argument('--edge',type=float,default=72)
    parser.add_argument('--login-top',type=float)
    parser.add_argument('--error-shown',action='store_true')
    args=parser.parse_args()
    with Image.open(args.shot) as shot, Image.open(args.background) as background:
        rows=check(shot,background,args.scale,args.edge,args.login_top,args.error_shown)
    for row in rows:
        print(f'{row["element"]:20s} leftmost ink={row["leftmost_ink"]} '+('OK' if row['passed'] else 'FAIL'))
    return 0 if all(row['passed'] for row in rows) else 1


if __name__=='__main__':
    raise SystemExit(main())
