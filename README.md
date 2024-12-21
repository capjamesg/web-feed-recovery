# Web Feed Recovery

This repository contains a script that aims to find a new version of a web feed for a feed that currently returns a 404.

This repository takes a list of feed URLs that are known to be 404s and attempts to find new feeds.

On a test of 160 broken feeds from the real-world, this project recovered 67%.

## Installation

First, clone this project:

```
git clone https://github.com/capjamesg/web-feed-recovery
```

Then, create a file called `feeds.txt` and add feeds that are known to be broken. Add one feed URL per line.

Then, run:

```
app.py
```

Results will be saved to a file called `results.json` with the structure:

```json
[
  {
    "original_feed": "https://blog.autumnrain.cc",
    "found_feeds": {
        "https://blog.autumnrain.cc/rss/": "application/rss+xml"
    }
  }
]
```

The key-value pairs are the found feed URL mapped to the found MIME type.

MIME types are only added if a feed was found through HTTP header discovery. If the feed was not found through HTTP header discovery, the MIME type will be null.

## Algorithm

1. Go to the homepage of the site associated with the feed.
2. Check the HTTP headers and HTML `<meta>` tags for signals of a feed (using the [indieweb-utils feed discovery implementation](https://indieweb-utils.readthedocs.io/en/latest/discovery.html#indieweb_utils.discover_web_page_feeds)).
3. Check for instances of several link anchors indicative of a feed (i.e. "RSS", "RSS Feed"). Save those as potential new feeds.
4. Check for instances of link anchors for several blog-related terms, like "Blog" and "Writing". Go to those pages, perform HTTP header and HTML meta tag analysis, and save any feeds.
5. Present all discovered feeds.

### Limitations

For a multi-user site on the same domain, the algorithm will not work. This is because a feed on the URL cannot be confidently, generally reconciled with a single writer with the algorithm above. More additions would be needed to support such behaviour.

## UX

The feeds returned are "potential" feeds, since any feed that the user did not add to a feed reader themselves (or that a feed reader did not infer from a URL provided by a user) cannot be known to be the right replacement without confirmation from a user. Thus, use of this script in any project should be accompanied by a stage where a user is asked to confirm that the new feed matches their expectations before replacing the broken feed with the newly-found one.

## License

This project is licensed under an [MIT license](LICENSE).
