def filter_urls(urls, include_keywords=None, exclude_keywords=None):
    filtered_urls = urls

    if include_keywords:
        filtered_urls = [url for url in filtered_urls if any(keyword.lower() in url.lower() for keyword in include_keywords)]
        print(f"\nURLs incluses (contenant {', '.join(include_keywords)}):")
        for url in filtered_urls:
            print(url)
    else:
        print("\nAucun mot-clé d'inclusion spécifié, toutes les URLs sont conservées.")

    if exclude_keywords:
        excluded_urls = [url for url in filtered_urls if any(keyword.lower() in url.lower() for keyword in exclude_keywords)]
        filtered_urls = [url for url in filtered_urls if url not in excluded_urls]
        print(f"\nURLs exclues (contenant {', '.join(exclude_keywords)}):")
        for url in excluded_urls:
            print(url)
    else:
        print("\nAucun mot-clé d'exclusion spécifié, aucune URL n'est exclue.")

    return filtered_urls