### Arachnyx Crawler

A simple, multithreaded web crawler written in Python. It can crawl websites, search for specific text, download images, and filter URLs.

#### Usage:

```bash
python3 crawler.py [options] <start_url>
```

**Options:**

* `-s TEXT, --search TEXT`: Search for `TEXT` in page HTML and save matching links to `matches.txt`.
* `-t N, --threads N`: Number of worker threads (default: 4).
* `-a AGENT, --agent AGENT`: Custom user-agent string.
* `-u TEXT, --url TEXT`: Only include URLs containing `TEXT`.
* `-i, --images`: Download all images to the `/images/` directory.
* `-h, --help`: Show help message and exit.

**Example:**

```bash
python3 crawler.py -s "Python" -t 8 -i https://www.python.org
```
