"""Create a standalone, printable HTML book from the maintained Markdown sources."""

import html
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
CSS = """
:root { color-scheme: light; }
body { margin:0; color:#172532; background:#edf1f3; font:17px/1.65 Georgia,serif; }
main { max-width:1000px; margin:auto; padding:48px 60px; background:white; }
h1,h2,h3,h4,nav { font-family:Arial,sans-serif; line-height:1.25; }
h1 { font-size:32px; color:#153d54; margin:0 0 24px; }
h2 { font-size:24px; margin-top:36px; }
h3 { font-size:20px; margin-top:28px; }
p,li { max-width:85ch; }
a { color:#075c89; text-underline-offset:3px; }
pre { overflow:auto; padding:16px; background:#f3f5f7; border-left:4px solid #28789b;
      white-space:pre-wrap; overflow-wrap:anywhere; font:13px/1.6 Consolas,monospace; }
code { font-family:Consolas,monospace; font-size:.88em; }
table { width:100%; border-collapse:collapse; margin:20px 0; font:14px/1.5 Arial,sans-serif; }
th { background:#153d54; color:white; text-align:left; }
td,th { border:1px solid #ccd7de; padding:10px; vertical-align:top; overflow-wrap:anywhere; }
tr:nth-child(even) td { background:#f5f8fa; }
nav { border:1px solid #ccd7de; padding:20px; margin-bottom:40px; }
section { padding-top:30px; margin-top:30px; border-top:2px solid #ccd7de; }
.label { font:12px Arial,sans-serif; letter-spacing:2px; color:#476577; }
@media(max-width:700px) { main { padding:24px 18px; } table { font-size:12px; } }
@media print {
  @page { size:A4; margin:18mm; }
  body { background:white; font-size:10pt; line-height:1.5; }
  main { padding:0; max-width:none; }
  section { break-before:page; border:0; padding:0; }
  h1,h2,h3,h4 { break-after:avoid; }
  h1 { font-size:25px; margin-bottom:18px; }
  h2 { font-size:20px; margin-top:24px; }
  h3 { font-size:17px; margin-top:20px; }
  pre { font-size:8pt; line-height:1.45; padding:12px; border-color:#888; break-inside:avoid; }
  table { font-size:8.5pt; }
  td,th { padding:7px; }
  tr { break-inside:avoid; }
  th { background:#e6edf1; color:black; }
}
"""


def build():
    contents = []
    sections = []
    for index, path in enumerate(FILES):
        source = path.read_text(encoding="utf-8")
        title = source.splitlines()[0].lstrip("# ")
        anchor = f"chapter-{index}"
        contents.append(f'<li><a href="#{anchor}">{html.escape(title)}</a></li>')
        # Local Markdown chapter links become links inside the standalone book.
        for other_index, other in enumerate(FILES):
            source = source.replace(f"(docs/{other.name})", f"(#chapter-{other_index})")
        body = markdown.markdown(source, extensions=["tables", "fenced_code"])
        sections.append(f'<section id="{anchor}">{body}</section>')
    document = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Jenkins + Python — Days 1 and 2</title><style>{CSS}</style></head><body><main>'
        '<p class="label">PRACTICAL TEACHING PACK · FIRST TWO DAYS</p>'
        '<h1>Jenkins + Python<br>From tested code to a verified release</h1>'
        '<p>Two 6½-hour teaching days · Theory cards · Guided labs · Failure diagnosis</p>'
        '<nav aria-label="Contents"><h2>Contents</h2><ol>' + ''.join(contents) + '</ol></nav>'
        + ''.join(sections) + '</main></body></html>'
    )
    target = ROOT / "dist" / "workshop-days-1-2.html"
    target.parent.mkdir(exist_ok=True)
    target.write_text(document, encoding="utf-8")
    print(target)


if __name__ == "__main__":
    build()
