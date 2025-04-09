from urllib.parse import urlparse

def filter_urls(urls, base_url):
    parsed_base = urlparse(base_url)
    return [url for url in urls if urlparse(url).netloc == parsed_base.netloc]

def exclude_urls_by_keywords(urls, keywords):
    return [url for url in urls if not any(keyword.lower() in url.lower() for keyword in keywords)]
