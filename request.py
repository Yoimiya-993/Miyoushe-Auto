headers = {
    'User-Agent': 'okhttp/4.9.3'
}


def get_new_session():
    import requests
    from requests.adapters import HTTPAdapter
    http_client = requests.Session()
    http_client.headers.update(headers)
    http_client.mount('http://', HTTPAdapter(max_retries=10))
    http_client.mount('https://', HTTPAdapter(max_retries=10))
    return http_client


http = get_new_session()
