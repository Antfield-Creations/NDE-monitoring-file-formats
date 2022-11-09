from urllib.request import urlopen


def get(url: str) -> str:
    """
    Simple helper function to get the text as utf-8 from a url
    :param url: The resource to get the text from

    :return: The response text, parsed as UTF-8
    """
    with urlopen(url) as f:
        if f.status != 200:
            raise RuntimeError(f'Invalid response {f.status}')

        res_text = f.read().decode('utf-8')
    return res_text
