from pathlib import Path

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

def input_make():
    prefix = input("Enter PREFIX (e.g., https://example.com/cast/album/): ")
    suffix = input("Enter SUFFIX (e.g., /): ")
    
    try:
        start = int(input("Enter START (e.g., 3301): "))
        end = int(input("Enter END (e.g., 3400): "))
    except ValueError:
        print("Error: START and END must be valid integer numbers.")
        return

    outfile = Path(f"links_{start}_{end}.html")
    html = build_html(prefix, suffix, start, end)
    outfile.write_text(html, encoding="utf-8")
    print(f"File made: {outfile.resolve()} ({end-start+1} links)")

if __name__ == "__main__":
    input_make()
