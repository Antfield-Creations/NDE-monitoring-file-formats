from http.client import HTTPSConnection

from retry import retry


@retry(tries=3, delay=1, backoff=2)
def get(url: str, conn: HTTPSConnection) -> str:
    """
    Simple helper function to get the text as utf-8 from a url
    :param url: The resource to get the text from
    :param conn: An initialized http.client.HTTPSConnection, as `conn = HTTPSConnection("example.com")`

    :return: The response text, parsed as UTF-8
    """
    conn.request(method="GET", url=url)
    response = conn.getresponse()
    if response.status != 200:
        raise RuntimeError(f'Invalid response {response.status}')

    res_text = response.read().decode('utf-8')
    return res_text
