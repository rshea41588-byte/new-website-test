#!/usr/bin/env python3
"""
render_shea_posts.py — GBP POSTS renderer for Shea Business Solutions.

Adapted from ~/an-irrigation-rebuild/tooling/render_posts.py (same 1080x810
4:3 spec, 2x Playwright render -> PIL LANCZOS -> JPEG q90, same fit-title +
contact-sheet QA). Difference: Shea is a no-photo trade (bookkeeping), so the
photo layer is replaced by a DESIGNED background — charcoal ledger-grid base
with an abstract gold bar-chart motif echoing the SBS logo mark. Clearly a
design, never a fake photo. Motif varies deterministically per post via
motif_seed so the batch reads as one family with distinct images.

Usage: python3 render_shea_posts.py --config posts.json --out <dir>
"""
import argparse, base64, io, json, mimetypes, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

CANVAS_W, CANVAS_H = 1080, 810
SCALE = 2
THUMB_W, THUMB_H = 270, 203
SHEET_COLS = 4
HEAD_MAX_STEPS = [96, 86, 76, 68, 60, 54, 48]
HEAD_BOX_H = 300

def die(m): print(f"ERROR: {m}", file=sys.stderr); sys.exit(1)

def data_uri(path):
    p = Path(path)
    if not p.is_file(): die(f"asset not found: {path}")
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    if p.suffix.lower() == ".svg": mime = "image/svg+xml"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def mix(a, b, t): return tuple(round(x + (y - x) * t) for x, y in zip(a, b))
def rgb_css(c, a=None): return f"rgb({c[0]},{c[1]},{c[2]})" if a is None else f"rgba({c[0]},{c[1]},{c[2]},{a})"

def rel_lum(c):
    def ch(v):
        v /= 255
        return v/12.92 if v <= 0.03928 else ((v+0.055)/1.055)**2.4
    r, g, b = (ch(x) for x in c)
    return 0.2126*r + 0.7152*g + 0.0722*b

def contrast(a, b):
    la, lb = sorted((rel_lum(a), rel_lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def esc(s):
    return (str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;"))

def motif_svg(seed, accent, accent2):
    """Abstract gold bar-chart crossing a baseline (echoes the SBS logo mark)
    + a thin rising polyline. Deterministic per seed."""
    rnd = random.Random(seed)
    n = 9
    bw = 46
    gap = 26
    x0 = 40
    base_y = 430
    bars = []
    for i in range(n):
        h = rnd.randint(60, 300)
        up = rnd.random() < 0.62
        alpha = rnd.choice([0.28, 0.42, 0.62, 0.85])
        col = accent2 if rnd.random() < 0.3 else accent
        x = x0 + i * (bw + gap)
        if up:
            bars.append(f'<rect x="{x}" y="{base_y-h}" width="{bw}" height="{h}" fill="{col}" fill-opacity="{alpha}" rx="3"/>')
        else:
            bars.append(f'<rect x="{x}" y="{base_y}" width="{bw}" height="{int(h*0.55)}" fill="{col}" fill-opacity="{alpha*0.7}" rx="3"/>')
    # rising polyline over the bars
    pts = []
    for i in range(n):
        x = x0 + i * (bw + gap) + bw // 2
        y = base_y - 40 - int((i / (n - 1)) * 240) + rnd.randint(-45, 45)
        pts.append(f"{x},{max(60, y)}")
    poly = f'<polyline points="{" ".join(pts)}" fill="none" stroke="{accent2}" stroke-opacity="0.9" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
    dots = "".join(f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="7" fill="{accent2}"/>' for p in [pts[0], pts[-1]])
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="810" viewBox="0 0 720 810">'
           f'<line x1="20" y1="{base_y}" x2="700" y2="{base_y}" stroke="{accent}" stroke-opacity="0.55" stroke-width="3"/>'
           f'{"".join(bars)}{poly}{dots}</svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

HTML = """<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@700&family=Jost:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
.canvas{{position:relative;width:{W}px;height:{H}px;overflow:hidden;
  background:radial-gradient(1100px 700px at 78% 42%, {lift} 0%, {bg} 62%)}}
.grid{{position:absolute;inset:0;background:
  repeating-linear-gradient(0deg, {gridline} 0 1px, transparent 1px 54px),
  repeating-linear-gradient(90deg, {gridline} 0 1px, transparent 1px 108px)}}
.motif{{position:absolute;right:-30px;top:0;width:720px;height:810px}}
.scrim{{position:absolute;inset:0;background:
  linear-gradient(90deg,{s95} 0%,{s90} 34%,{s60} 55%,{s20} 74%,transparent 88%),
  linear-gradient(0deg,{s80} 0%,{s30} 20%,transparent 40%)}}
.content{{position:absolute;left:70px;right:70px;top:64px;bottom:60px;
  display:flex;flex-direction:column;justify-content:center;
  font-family:'{body_font}','Helvetica Neue',Arial,sans-serif;color:#fff}}
.eyebrow{{font-size:26px;font-weight:700;letter-spacing:4px;text-transform:uppercase;
  color:{accent};margin-bottom:22px}}
.headbox{{height:{head_h}px;display:flex;flex-direction:column;justify-content:center}}
.headline{{font-family:'{display_font}',Georgia,serif;font-weight:700;line-height:1.05;
  color:#fff;max-width:640px;text-shadow:0 2px 12px rgba(0,0,0,.55)}}
.divider{{width:88px;height:5px;background:{accent};border-radius:3px;margin:26px 0 30px}}
.foot{{display:flex;align-items:center;gap:22px}}
.foot img{{height:74px;width:auto;display:block}}
.sep{{width:1.5px;height:46px;background:rgba(255,255,255,.35);flex:0 0 auto}}
.phone{{font-size:24px;font-weight:600;color:{accent2};letter-spacing:.5px}}
</style></head><body>
<div class="canvas">
  <div class="grid"></div>
  <img class="motif" src="{motif}">
  <div class="scrim"></div>
  <div class="content">
    <div class="eyebrow">{eyebrow}</div>
    <div class="headbox"><div class="headline" id="hl">{headline}</div></div>
    <div class="divider"></div>
    <div class="foot">
      <img src="{logo}">
      <span class="sep"></span>
      <span class="phone">{phone}</span>
    </div>
  </div>
</div></body></html>"""

FIT_JS = """(args)=>{const[steps,boxH,maxW]=args;const el=document.getElementById('hl');
const fits=()=>el.scrollHeight<=boxH&&el.scrollWidth<=maxW;let used=steps[steps.length-1];
for(const s of steps){el.style.fontSize=s+'px';if(fits()){used=s;break;}}return used;}"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    b = cfg["brand"]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    primary = hex_to_rgb(b["primary_hex"])
    accent = hex_to_rgb(b["accent_hex"])
    accent2 = hex_to_rgb(b.get("accent2_hex", b["accent_hex"]))
    bg = mix(primary, (0, 0, 0), 0.35)          # deep charcoal
    scrim = mix(primary, (0, 0, 0), 0.55)
    lift = mix(primary, accent, 0.10)
    cr = contrast((255, 255, 255), scrim)
    acr = contrast(accent, scrim)
    print(f"CONTRAST: white headline vs scrim = {cr:.2f}:1 (need >=4.5)  |  gold accent vs scrim = {acr:.2f}:1")
    if cr < 4.5: print("WARNING: headline contrast below 4.5:1")

    logo_uri = data_uri(b["logo_path"])
    acc_css, acc2_css = rgb_css(accent), rgb_css(accent2)

    rendered = []
    seen = set()
    prev_kw = None
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        page = br.new_page(viewport={"width": CANVAS_W, "height": CANVAS_H}, device_scale_factor=SCALE)
        for p in cfg["posts"]:
            combo = (p["motif_seed"], p["keyword"])
            if combo in seen: die(f"duplicate motif+keyword combo: {combo}")
            seen.add(combo)
            if p["keyword"] == prev_kw: die(f"keyword repeated back-to-back: {p['keyword']}")
            prev_kw = p["keyword"]
            html = HTML.format(
                W=CANVAS_W, H=CANVAS_H, head_h=HEAD_BOX_H,
                bg=rgb_css(bg), lift=rgb_css(lift, 0.9),
                gridline=rgb_css(accent, 0.05),
                s95=rgb_css(scrim, 0.95), s90=rgb_css(scrim, 0.90), s80=rgb_css(scrim, 0.80),
                s60=rgb_css(scrim, 0.60), s30=rgb_css(scrim, 0.30), s20=rgb_css(scrim, 0.20),
                accent=acc_css, accent2=acc2_css,
                motif=motif_svg(p["motif_seed"], acc_css, acc2_css),
                logo=logo_uri,
                display_font=esc(b["display_font"]), body_font=esc(b["body_font"]),
                eyebrow=esc(b["service_area"]), headline=esc(p["headline"]),
                phone=esc(b["phone"]),
            )
            page.set_content(html, wait_until="networkidle")
            page.evaluate("() => document.fonts.ready.then(() => true)")
            used = page.evaluate(FIT_JS, [HEAD_MAX_STEPS, HEAD_BOX_H, 640])
            raw = page.screenshot(type="png")
            img = Image.open(io.BytesIO(raw)).convert("RGB").resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
            dest = out / f"{p['key']}.jpg"
            img.save(dest, "JPEG", quality=90)
            rendered.append((p["key"], dest))
            print(f"rendered {dest.name}  (headline {used}px)")
        br.close()

    pad, lh = 18, 26
    cols = min(SHEET_COLS, len(rendered))
    rows = -(-len(rendered)//cols)
    sw = pad + cols*(THUMB_W+pad); sh = pad + rows*(THUMB_H+lh+pad)
    sheet = Image.new("RGB", (sw, sh), (238,240,242))
    d = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
    except OSError: font = ImageFont.load_default()
    for i,(k,pth) in enumerate(rendered):
        c,r = i%cols, i//cols
        x = pad + c*(THUMB_W+pad); y = pad + r*(THUMB_H+lh+pad)
        sheet.paste(Image.open(pth).resize((THUMB_W,THUMB_H), Image.LANCZOS), (x,y))
        d.rectangle([x,y,x+THUMB_W-1,y+THUMB_H-1], outline=(190,192,196))
        d.text((x+2,y+THUMB_H+6), k.replace("_"," ")[:46], fill=(30,32,36), font=font)
    sheet.save(out / "_contact-sheet.png", "PNG")
    print(f"rendered _contact-sheet.png ({sw}x{sh})")
    print(f"done: {len(rendered)} post images in {out}")

if __name__ == "__main__":
    main()
