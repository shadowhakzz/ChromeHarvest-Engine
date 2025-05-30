"""
Advanced Web Scraper
A powerful web scraping tool that can download complete web pages including all assets.
Supports both static and dynamic content, with automatic crawling capabilities.
"""

import os
import re
import time
import json
from urllib.parse import urljoin, urlparse, urlunparse, urldefrag

import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------- Basic utilities ----------

def setup_session(retries=3, backoff_factor=0.3, status_forcelist=(500,502,504), user_agent=None):
    """
    Set up a requests session with retry capabilities and custom user agent.
    
    Args:
        retries (int): Number of retry attempts
        backoff_factor (float): Time to wait between retries
        status_forcelist (tuple): HTTP status codes to retry on
        user_agent (str): Custom user agent string
    
    Returns:
        requests.Session: Configured session object
    """
    session = requests.Session()
    ua = user_agent or (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
    session.headers.update({'User-Agent': ua})
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def categorize_asset(path):
    """
    Categorize an asset based on its file extension.
    
    Args:
        path (str): File path or URL
    
    Returns:
        str: Category name (css, js, images, or assets)
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == '.css':   return 'css'
    if ext == '.js':    return 'js'
    if ext in ('.png','.jpg','.jpeg','.gif','.svg','.webp','.ico'): return 'images'
    return 'assets'


def make_local_path(base_dir, asset_url, base_url):
    """
    Create a local path for an asset URL.
    
    Args:
        base_dir (str): Base directory for saving files
        asset_url (str): URL of the asset
        base_url (str): Base URL of the page
    
    Returns:
        tuple: (local_path, real_url)
    """
    parsed = urlparse(asset_url)
    if not parsed.netloc:
        asset_url = urljoin(base_url, asset_url)
        parsed = urlparse(asset_url)
    rel_path = os.path.normpath(parsed.path.lstrip('/'))
    category = categorize_asset(rel_path)
    local_path = os.path.join(base_dir, category, rel_path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    return local_path, asset_url


def download_asset(session, url, local_path, delay):
    """
    Download an asset and save it to the local path.
    
    Args:
        session (requests.Session): Session object
        url (str): URL of the asset
        local_path (str): Local path to save the asset
        delay (float): Delay between downloads
    
    Returns:
        bool: True if download was successful
    """
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        with open(local_path, 'wb') as f:
            f.write(resp.content)
        time.sleep(delay)
        return True
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return False

# ---------- Dynamic URL collector via Selenium ----------

def get_dynamic_urls(page_url, wait, user_agent=None):
    """
    Collect dynamic URLs using Selenium.
    
    Args:
        page_url (str): URL of the page to scrape
        wait (float): Time to wait for dynamic content
        user_agent (str): Custom user agent
    
    Returns:
        set: Set of dynamic URLs
    """
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--disable-gpu")
    if user_agent:
        chrome_opts.add_argument(f"--user-agent={user_agent}")
    chrome_opts.add_experimental_option("perfLoggingPrefs", {"enableNetwork": True})
    chrome_opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_opts
    )
    driver.get(page_url)
    time.sleep(wait)

    logs = driver.get_log("performance")
    driver.quit()

    urls = set()
    for entry in logs:
        msg = json.loads(entry["message"])['message']
        if msg.get("method") == "Network.requestWillBeSent":
            u = msg["params"]["request"]["url"]
            if any(u.lower().endswith(ext) for ext in (
                ".css",".js",".png",".jpg",".jpeg",".woff",".woff2",".svg",".json"
            )):
                urls.add(u)
    return urls

# ---------- Main scraper combining both methods ----------

def scrape_page_combined(
    page_url,
    output_dir="downloaded_site",
    delay=0.5,
    wait_dynamic=2.0,
    user_agent=None
):
    """
    Scrape a web page and download all its assets.
    
    Args:
        page_url (str): URL of the page to scrape
        output_dir (str): Directory to save downloaded files
        delay (float): Delay between downloads
        wait_dynamic (float): Time to wait for dynamic content
        user_agent (str): Custom user agent
    """
    session = setup_session(user_agent=user_agent)

    # بدون توجه به robots.txt ادامه می‌دهیم

    # 1) Fetch initial HTML, fallback to Selenium if forbidden
    try:
        resp = session.get(page_url, timeout=10)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        html = resp.content
    except requests.exceptions.HTTPError as e:
        print(f"⚠️ HTTPError {e.response.status_code}, using Selenium fallback...")
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--disable-gpu")
        if user_agent:
            opts.add_argument(f"--user-agent={user_agent}")
        opts.add_experimental_option("perfLoggingPrefs", {"enableNetwork": True})
        opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=opts
        )
        driver.get(page_url)
        time.sleep(wait_dynamic)
        html = driver.page_source.encode('utf-8')
        driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    # 2) Collect static URLs
    static_urls = set()
    for tag, attr in [("link","href"),("script","src"),("img","src")]:
        for el in soup.find_all(tag):
            v = el.get(attr)
            if v and not v.startswith(("data:","javascript:")):
                static_urls.add(v)

    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href and not href.startswith("data:"):
            full_css = urljoin(page_url, href)
            try:
                css_txt = session.get(full_css).text
                for m in re.findall(r"url\(['\"]?(.*?)['\"]?\)", css_txt):
                    if m and not m.startswith("data:"):
                        static_urls.add(m)
            except:
                pass

    # 3) Collect dynamic URLs
    dynamic_urls = get_dynamic_urls(page_url, wait_dynamic, user_agent)

    all_urls = static_urls | dynamic_urls
    print(f"🔍 Found {len(static_urls)} static + {len(dynamic_urls)} dynamic = {len(all_urls)} total assets.")

    # 4) Download everything
    url_to_local = {}
    for u in tqdm(all_urls, desc="Downloading assets"):
        try:
            local_path, real_url = make_local_path(output_dir, u, page_url)
            if download_asset(session, real_url, local_path, delay):
                url_to_local[real_url] = local_path
        except Exception as e:
            print("⚠️", e)

    # 5) Update URLs in soup
    for tag, attr in [("img","src"),("script","src"),("link","href"),("a","href")]:
        for el in soup.find_all(tag):
            v = el.get(attr)
            if not v: continue
            full = urljoin(page_url, v)
            if full in url_to_local:
                rel = os.path.relpath(url_to_local[full], output_dir).replace(os.sep, "/")
                el[attr] = rel

    # 6) مرتب‌سازی و ذخیره نهایی HTML
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "index.html")

    # استفاده از prettify برای خوانایی بهتر HTML
    pretty_html = soup.prettify()

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(pretty_html)

    print(f"✅ Site saved to `{output_dir}` with {len(url_to_local)} assets.")

# ---------- Internal Link Crawler ----------

def scrape_with_crawling(
    start_url,
    output_dir="downloaded_site",
    delay=0.5,
    wait_dynamic=2.0,
    user_agent=None,
    max_pages=10
):
    """
    Crawl and scrape multiple pages starting from a URL.
    
    Args:
        start_url (str): Starting URL
        output_dir (str): Base directory for saving files
        delay (float): Delay between downloads
        wait_dynamic (float): Time to wait for dynamic content
        user_agent (str): Custom user agent
        max_pages (int): Maximum number of pages to crawl
    """
    visited = set()
    to_visit = [start_url]
    domain = urlparse(start_url).netloc

    count = 0
    while to_visit and count < max_pages:
        current = to_visit.pop(0)
        clean_url = urldefrag(current)[0]
        if clean_url in visited:
            continue
        print(f"\n🌐 Crawling ({count+1}/{max_pages}): {clean_url}")
        try:
            scrape_page_combined(
                page_url=clean_url,
                output_dir=os.path.join(output_dir, f"page_{count+1}"),
                delay=delay,
                wait_dynamic=wait_dynamic,
                user_agent=user_agent
            )
            visited.add(clean_url)
            count += 1
        except Exception as e:
            print(f"❌ Error scraping {clean_url}: {e}")
            continue

        session = setup_session(user_agent=user_agent)
        try:
            r = session.get(clean_url, timeout=10)
            soup = BeautifulSoup(r.content, "html.parser")
            for a in soup.find_all("a", href=True):
                href = urljoin(clean_url, a['href'])
                parsed = urlparse(href)
                if parsed.netloc == domain and urldefrag(href)[0] not in visited:
                    to_visit.append(href)
        except:
            continue

    print(f"\n✅ Finished crawling {count} pages.")

# ---------- CLI ----------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Web Scraper")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--output", "-o", default="downloaded_site", help="Output directory")
    parser.add_argument("--delay", "-d", type=float, default=0.5, help="Delay between downloads")
    parser.add_argument("--wait", "-w", type=float, default=2.0, help="Wait time for dynamic content")
    parser.add_argument("--crawl", "-c", action="store_true", help="Enable crawling")
    parser.add_argument("--max-pages", "-m", type=int, default=10, help="Maximum pages to crawl")
    parser.add_argument("--user-agent", "-u", help="Custom user agent")
    
    args = parser.parse_args()
    
    if args.crawl:
        scrape_with_crawling(
            start_url=args.url,
            output_dir=args.output,
            delay=args.delay,
            wait_dynamic=args.wait,
            user_agent=args.user_agent,
            max_pages=args.max_pages
        )
    else:
        scrape_page_combined(
            page_url=args.url,
            output_dir=args.output,
            delay=args.delay,
            wait_dynamic=args.wait,
            user_agent=args.user_agent
        )
