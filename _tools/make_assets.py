"""make_assets.py -- regenerate the website's derived images from the originals.

Where it sits: originals in images/  ->  this script  ->  right-sized copies, icons and
the social-preview card that index.html links to. Not published: Jekyll (GitHub Pages)
skips folders whose names start with "_".
Inputs:  images/headshot.png (1225x1225, photo inside a circle on black),
         images/Ultrasound_Watermark.jpg (2031x994).
Outputs: images/headshot-256.jpg, images/headshot-512.jpg, images/Ultrasound_Watermark-1000.jpg,
         images/og-card.png (1200x630), favicon-32.png, apple-touch-icon.png (180x180).
Run from the repo root:  python3 _tools/make_assets.py
"""
import os                                                            # [L] os.path checks, not pathlib: three paths only, keeps it short
from PIL import Image, ImageDraw, ImageFont, ImageOps                # [L] Pillow: already installed here; no extra dependency

ACCENT = (181, 71, 11)                                               # [L] #b5470b burnt orange: 5.4:1 contrast on white, the site's accent
INK = (29, 29, 31)                                                   # [L] #1d1d1f near-black body text: 16.8:1 on white
INK_2 = (74, 74, 79)                                                 # [L] #4a4a4f secondary text: 8.9:1 on white, not light grey (slide: avoid gray-on-gray)
PAPER = (250, 247, 244)                                              # [L] #faf7f4 warm off-white, echoes the photo's sunset


def font(names, size):
    """Return the first available TrueType font from `names` at `size` px.

    names: list of file paths, tried in order (system fonts differ between Macs).
    size:  pixel height of the font (int).
    Method: try each path; ImageFont.truetype raises OSError if missing.
    Alternatives: ImageFont.load_default() -- a tiny bitmap font, unreadable on a 1200 px card.
    """
    for n in names:                                                  # [L] first font that exists wins
        try:
            return ImageFont.truetype(n, size)
        except OSError:                                              # [L] OSError = file not found / unreadable; try the next one
            continue
    return ImageFont.load_default()                                  # [L] last resort so the script never crashes


SERIF_BOLD = ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf", "/Library/Fonts/Georgia Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]   # [L] Georgia, not Arial, for the name: echoes the site's serif headings
SANS = ["/System/Library/Fonts/Supplemental/Arial.ttf"]              # [L] Arial for body text on the card
SANS_BOLD = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf"]


def inner_circle_crop(img, inset_frac=0.02):
    """Crop the photo to the square that tightly holds its circle, minus a small inset.

    img:        RGB PIL image of the headshot (photo circle on a black square).
    inset_frac: fraction of the circle's diameter trimmed from each side (0.02 = 2 %),
                so dark anti-aliased edge pixels don't show as a thin black ring once
                CSS rounds the corners again.
    Returns:    square RGB image.
    Method: threshold brightness > 20 (black background is ~0) and take the bounding
            box of everything brighter -- that box is the circle's bounding square.
    Alternatives: hard-coded pixel numbers (break if the photo changes).
    """
    mask = img.convert("L").point(lambda v: 255 if v > 20 else 0)    # [L] 20 of 255: just above pure black, so JPEG noise isn't counted as photo
    left, top, right, bottom = mask.getbbox()                        # [L] bounding box of the photo circle, in px
    d = min(right - left, bottom - top)                              # [L] circle diameter in px
    inset = int(d * inset_frac)                                      # [L] e.g. 2 % of 1125 px ~ 22 px trimmed per side
    return img.crop((left + inset, top + inset, left + d - inset, top + d - inset))


def save_jpeg(img, path, width):
    """Resize `img` to `width` px wide (keeping its aspect ratio) and save as JPEG quality 85."""
    h = round(img.height * width / img.width)                        # [L] keep aspect ratio: new height = old height x scale
    img.resize((width, h), Image.LANCZOS).save(path, quality=85, optimize=True)  # [L] LANCZOS, not NEAREST: sharp downscaling; q85 ~ visually lossless at a third of q100's size
    print(f"wrote {path}: {width}x{h}, {os.path.getsize(path):,} bytes")


def wrap(draw, text, fnt, max_w):
    """Split `text` into lines no wider than `max_w` px when drawn with `fnt`."""
    lines, line = [], ""
    for word in text.split():                                        # [L] greedy word wrap: add words until the line would overflow
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line]


def main():
    # Step 1: right-sized headshots (256 px for normal screens, 512 px for 2x Retina)
    head = inner_circle_crop(Image.open("images/headshot.png").convert("RGB"))
    for w in (256, 512):                                             # [L] displayed at <= 220 CSS px, so 256 (1x) and 512 (2x) cover every screen
        save_jpeg(head, f"images/headshot-{w}.jpg", w)

    # Step 2: lighter copy of the widest research figure (2031 px is ~3x what the page shows)
    save_jpeg(Image.open("images/Ultrasound_Watermark.jpg").convert("RGB"), "images/Ultrasound_Watermark-1000.jpg", 1000)

    # Step 3: favicons -- "RG" monogram on the accent colour
    for size, path in ((32, "favicon-32.png"), (180, "apple-touch-icon.png")):  # [L] 32 px browser tab; 180 px is Apple's home-screen icon size
        icon = Image.new("RGB", (size, size), ACCENT)                # [L] opaque square, not transparent: iOS fills transparency with black
        d = ImageDraw.Draw(icon)
        f = font(SERIF_BOLD, int(size * 0.5))                        # [L] letters at half the icon height stay legible at 32 px
        d.text((size / 2, size / 2), "RG", font=f, fill="white", anchor="mm")  # [L] anchor "mm" = centre the text on that point
        icon.save(path)
        print(f"wrote {path}: {size}x{size}")

    # Step 4: social-preview card, 1200x630 (the size LinkedIn, Slack, iMessage and X expect)
    W, H = 1200, 630
    card = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(card)
    d.rectangle((0, 0, 16, H), fill=ACCENT)                          # [L] 16 px accent bar on the left edge ties the card to the site
    photo = head.resize((360, 360), Image.LANCZOS)                   # [L] 360 px photo ~ 57 % of the card height
    mask = Image.new("L", (360, 360), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 359, 359), fill=255)         # [L] circular mask, not a square photo: matches the site
    card.paste(photo, (80, 135), mask)                               # [L] (80, 135): vertically centred, (630 - 360) / 2 = 135
    x = 500                                                          # [L] text column starts 60 px right of the photo
    d.text((x, 150), "Rishav Gupta", font=font(SERIF_BOLD, 66), fill=INK)
    d.text((x, 238), "Ph.D. Student in Computer Science, UMBC", font=font(SANS_BOLD, 30), fill=ACCENT)
    blurb = ("Turning everyday smartphones into cardiovascular sensors, using only "
             "the phone's own speaker and microphone.")
    y = 300
    for line in wrap(d, blurb, font(SANS, 30), W - x - 70):          # [L] 70 px right margin keeps text off the edge
        d.text((x, y), line, font=font(SANS, 30), fill=INK_2)
        y += 42                                                      # [L] 42 px line spacing = 1.4 x the 30 px font
    d.text((x, y + 30), "riishavguptaa.com", font=font(SANS_BOLD, 28), fill=ACCENT)
    card.save("images/og-card.png", optimize=True)
    print(f"wrote images/og-card.png: {W}x{H}, {os.path.getsize('images/og-card.png'):,} bytes")


if __name__ == "__main__":
    main()
