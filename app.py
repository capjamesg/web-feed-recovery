import requests
import concurrent.futures
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import tqdm
import indieweb_utils
import json

with open("failed.txt", "r") as f:
    broken_feeds = f.read().splitlines()

broken_feeds = list(set([i.replace("&gt;", "") for i in broken_feeds if i]))

INDICATIVE_TERMS = [
    "rss",
    "atom",
    "feed",
    "rss feed",
    "atom feed",
]


def canonicalize_url(url, domain):
    if isinstance(url, tuple):
        url = url[0]

    if not url.startswith("http"):
        url = "/" + url

    if url.startswith("/"):
        return urljoin("https://" + domain, url)

    return url


def get_page_title(feed):
    homepage = urlparse(feed).netloc
    protocol = urlparse(feed).scheme
    if not protocol:
        feed = f"https://{homepage}"
    else:
        feed = f"{protocol}://{homepage}"

    try:
        response = requests.get(feed, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {feed}")
        return feed, None

    return feed, response


def feed_inference(url):
    try:
        feeds = indieweb_utils.discover_web_page_feeds(url)
    except Exception as e:
        # print(f"Failed to infer feeds from {url}")
        return []

    return feeds


def search_for_indicative_terms(content, url):
    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.find_all("a", href=True)
    found_feeds = {}

    for link in links:
        if any(term in link.get_text() for term in INDICATIVE_TERMS):
            found_feeds[link.get("href")] = link.get("type")

    return found_feeds.items()


def search_for_blog(content, url):
    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.find_all("a", href=True) + soup.find_all(
        "a",
        string=lambda text: text
        and any(
            term in text.lower() for term in ["blog", "writing"] + INDICATIVE_TERMS
        ),
    )
    found_blogs = []

    for link in links:
        # if blog in body text of link, or "xml" in url
        if (
            "blog" in link.get_text().lower()
            or "writing" in link.get_text().lower()
            or "xml" in link.get("href")
        ):
            found_blogs.append(link.get("href"))

    found_blogs = [canonicalize_url(blog, urlparse(url).netloc) for blog in found_blogs]

    # run feed inference on found blogs
    found_blogs = list(set(found_blogs))
    results = {}

    for blog in found_blogs[:3]:
        result = feed_inference(blog)
        for feed in result:
            results[feed.url] = feed.mime_type

    for feed in search_for_indicative_terms(content, url):
        results[feed] = None

    return results


with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    results = list(
        tqdm.tqdm(executor.map(get_page_title, broken_feeds), total=len(broken_feeds))
    )

failed_count = 0
all_reconciled_feeds = []

for feed_url, response in results:
    if response is None:
        continue

    if urlparse(feed_url).scheme not in ["http", "https"]:
        continue

    content = response.content

    if response.status_code not in [200, 301, 302, 404]:
        print(f"Failed to fetch {feed_url}")
        continue

    found_feeds = {}

    identified_feeds_from_inference = feed_inference(feed_url)

    for feed in identified_feeds_from_inference:
        found_feeds[feed.url] = feed.mime_type

    identified_feeds_from_terms = search_for_indicative_terms(content, feed_url)

    for feed, mime_type in identified_feeds_from_terms:
        found_feeds[feed] = mime_type

    identified_blogs = search_for_blog(content, feed_url)

    found_feeds.update(identified_blogs)

    found_feeds = {
        canonicalize_url(feed, urlparse(feed_url).netloc): mime_type
        for feed, mime_type in found_feeds.items()
    }

    if not found_feeds:
        # print("Failed to find feeds for", feed_url)
        failed_count += 1
    if found_feeds:
        print(feed_url, found_feeds)

    all_reconciled_feeds.append({"original_url": feed_url, "found_feeds": found_feeds})

print("Count: ", failed_count)
print("Rate of feeds potentially recoverable: ", (len(broken_feeds) - failed_count) / len(broken_feeds))

with open("results.json", "w") as f:
    json.dump(all_reconciled_feeds, f, indent=4)
