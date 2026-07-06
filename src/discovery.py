from bs4 import BeautifulSoup
from urllib.parse import urljoin


def discover_meeting_urls(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")

    meeting_urls = set()

    for link in soup.find_all("a", href=True):
        href = urljoin(base_url, link["href"])

        if "adminmonitor.com/tx/puct/open_meeting/" in href:
            meeting_urls.add(href.rstrip("/") + "/")

    return sorted(meeting_urls)