import requests
from bs4 import BeautifulSoup

def test_request(url, tag_name='none'):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }

    print(f"Testing {tag_name}...")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Length: {len(resp.text)}")
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = soup.title.string if soup.title else 'No Title'
        print(f"Title: {title.strip() if title else ''}")
    except Exception as e:
        print(f"Error: {e}")

test_request("http://www.uop.edu.pk/news/", "Standard requests")
