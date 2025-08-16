from pathlib import Path

PREFIX = "https://concursos.estrategia.com/cast/album/"
SUFFIX = "/"
START = 2909
END = 3300
OUTFILE = Path("links_{}_{}.html".format(START, END))

def build_html(prefix: str, suffix: str, start: int, end: int) -> str:
    links = [f"{prefix}{n}{suffix}" for n in range(start, end + 1)]
    items = "\n    ".join(f'<li><a href="{u}" target="_blank">{u}</a></li>' for u in links)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lista de Links ({start} a {end})</title>
</head>
<body>
  <h1>Lista de Links</h1>
  <div>Total: {len(links)} links ({start} a {end})</div>
  <ul>
    {items}
  </ul>
</body>
</html>"""

def main():
    html = build_html(PREFIX, SUFFIX, START, END)
    OUTFILE.write_text(html, encoding="utf-8")
    print(f"File made: {OUTFILE.resolve()} ({END-START+1} links)")

if __name__ == "__main__":
    main()
