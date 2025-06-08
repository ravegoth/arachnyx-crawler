import sys
import os
import random
import requests
import threading
import argparse
import signal
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from colorama import init, Fore, Style
from queue import Queue, Empty

# init colorama
init(autoreset=True)

# global containers
queue_urls = Queue()
visited = set()
lock = threading.Lock()

# file paths
crawled_file = 'crawled.txt'
matches_file = 'matches.txt'
images_dir = 'images'

# flag for stopping
stop_event = threading.Event()


def print_usage():
    print(Style.BRIGHT + Fore.CYAN + "arachnyx crawler usage:")
    print(Fore.YELLOW + "  crawler.py [options] <start_url>")
    print(Fore.MAGENTA + "options:")
    print(Fore.GREEN + "  -s TEXT, --search TEXT" + Fore.WHITE + "    search for TEXT in page html, save matching links to matches.txt")
    print(Fore.GREEN + "  -t N, --threads N" + Fore.WHITE + "    number of worker threads (default: 4)")
    print(Fore.GREEN + "  -a AGENT, --agent AGENT" + Fore.WHITE + "    custom user-agent string")
    print(Fore.GREEN + "  -u TEXT, --url TEXT" + Fore.WHITE + "    only include urls containing TEXT")
    print(Fore.GREEN + "  -i, --images" + Fore.WHITE + "    download all images to /images/")
    print(Fore.GREEN + "  -h, --help" + Fore.WHITE + "    show this help and exit")


def legit_link(link: str) -> bool:
    """check if link looks crawl-worthy, including protocol-relative"""
    if not link or link.startswith('#'):
        return False
    if link.startswith('//'):
        return True
    parsed = urlparse(link)
    return parsed.scheme in {'http', 'https'}


def scrape(url: str, agent: str, search_term: str, download_images: bool) -> list:
    """
    fetch url, extract links, log crawled url,
    search term, download images if needed
    """
    headers = {'user-agent': agent}
    fresh = []
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')

        # search for term
        if search_term and search_term in html:
            with lock:
                with open(matches_file, 'a') as mf:
                    mf.write(f"{url}\n")
            print(Fore.BLUE + f"* found '{search_term}' in {url}")

        # download images
        if download_images:
            os.makedirs(images_dir, exist_ok=True)
            for img in soup.find_all('img', src=True):
                raw = img['src']
                if not legit_link(raw):
                    continue
                img_url = urljoin(url, raw)
                try:
                    img_resp = requests.get(img_url, headers=headers, timeout=10)
                    img_resp.raise_for_status()
                    fname = os.path.basename(urlparse(img_url).path) or 'unnamed'
                    path = os.path.join(images_dir, fname)
                    with open(path, 'wb') as f:
                        f.write(img_resp.content)
                    print(Fore.MAGENTA + f"+ downloaded image: {fname}")
                except Exception:
                    pass

        # extract links
        for tag in soup.find_all('a', href=True):
            raw = tag.get('href')
            if not legit_link(raw):
                continue
            abs_url = urljoin(url, raw)
            with lock:
                if abs_url not in visited:
                    fresh.append(abs_url)
    except Exception as e:
        print(Fore.RED + f"! failed {url}: {e}")
    # log crawled
    with lock:
        with open(crawled_file, 'a') as cf:
            cf.write(f"{url}\n")
    return fresh


def worker(agent: str, search_term: str, url_filter: str, download_images: bool):
    while not stop_event.is_set():
        try:
            current = queue_urls.get(timeout=1)
        except Empty:
            continue

        with lock:
            if current in visited:
                queue_urls.task_done()
                continue
            visited.add(current)

        new_links = scrape(current, agent, search_term, download_images)
        count_new = 0
        for link in new_links:
            if url_filter and url_filter not in link:
                continue
            with lock:
                if link not in visited:
                    queue_urls.put(link)
                    count_new += 1

        print(Fore.GREEN + f"< {current} - {count_new} new links, queue: {queue_urls.qsize()}")
        queue_urls.task_done()


def sigint_handler(sig, frame):
    print(Fore.YELLOW + "\nbye, crawl session ended.")
    stop_event.set()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-s', '--search', dest='search', help='search term', default='')
    parser.add_argument('-t', '--threads', dest='threads', type=int, default=4, help='number of threads')
    parser.add_argument('-a', '--agent', dest='agent', default='arachnyx-crawler/0.1', help='user-agent string')
    parser.add_argument('-u', '--url', dest='url_filter', help='url filter text', default='')
    parser.add_argument('-i', '--images', dest='images', action='store_true', help='download images')
    parser.add_argument('-h', '--help', action='store_true', dest='help')
    parser.add_argument('start_url', nargs='?')
    args = parser.parse_args()

    if args.help or not args.start_url:
        print_usage()
        sys.exit(0)

    start = args.start_url
    queue_urls.put(start)

    print(Style.BRIGHT + Fore.MAGENTA + "arachnyx crawler")
    print(Fore.CYAN + f"starter:\n> {start}")

    # clear logs and create images dir if needed
    open(crawled_file, 'w').close()
    open(matches_file, 'w').close()
    if args.images:
        os.makedirs(images_dir, exist_ok=True)

    # start threads
    for _ in range(args.threads):
        t = threading.Thread(target=worker, args=(args.agent, args.search, args.url_filter, args.images), daemon=True)
        t.start()

    # wait indefinitely until ctrl+c
    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        sigint_handler(None, None)


if __name__ == '__main__':
    main()