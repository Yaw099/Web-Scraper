from bs4 import BeautifulSoup
from urllib.parse import urljoin


def extract_structured_content(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    lines: list[str] = []

    title = soup.find("title")
    if title:
        lines.append(f"# Page Title\n{title.get_text(strip=True)}\n")

    lines.append("# Headings")
    for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = heading.get_text(" ", strip=True)
        if text:
            lines.append(f"- {text}")

    lines.append("\n# Paragraphs")
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True)
        if text:
            lines.append(text)

    lines.append("\n# Tables")
    for index, table in enumerate(soup.find_all("table"), start=1):
        lines.append(f"\n## Table {index}")
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            values = [cell.get_text(" ", strip=True) for cell in cells]
            if values:
                lines.append(" | ".join(values))

    lines.append("\n# Links")
    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = urljoin(url, link["href"])
        if text:
            lines.append(f"- {text}: {href}")

    lines.append("\n# Full Visible Text")
    lines.append(soup.get_text("\n", strip=True))

    return "\n".join(lines)
