"""Instructor layout QA: page summary and rendered contact sheets."""

from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def inspect():
    source = ROOT / "output/pdf/workshop-days-1-2.pdf"
    with pdfplumber.open(source) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        for index, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if not text.strip():
                raise ValueError(f"Blank page: {index}")
            if '\u25a0' in text or '\ufffd' in text:
                raise ValueError(f"Suspicious replacement glyph on page {index}")
            print(f"{index}: {text.splitlines()[0][:80]}")
    images = sorted((ROOT / "tmp/pdfs").glob("final-page-*.png"))
    if not images:
        images = sorted((ROOT / "tmp/pdfs").glob("page-*.png"))
    for start in range(0, len(images), 16):
        sheet = Image.new("RGB", (1200, 1800), "#d7dde2")
        draw = ImageDraw.Draw(sheet)
        for offset, path in enumerate(images[start:start + 16]):
            image = Image.open(path).convert("RGB")
            image.thumbnail((280, 410))
            x, y = (offset % 4) * 300 + 10, (offset // 4) * 450 + 25
            sheet.paste(image, (x, y))
            draw.text((x, y - 20), f"Page {start + offset + 1}", fill="black")
        output = ROOT / "tmp/pdfs" / f"contact-{start // 16 + 1}.png"
        sheet.save(output)
        print(output)


if __name__ == "__main__":
    inspect()
