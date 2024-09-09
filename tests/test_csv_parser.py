from analysis.common_crawl import parse_csv

sample = [
    {'crawl': 'CC-MAIN-2017-22', 'mimetype_detected': '<other>', 'pages': '410273', 'urls': '408769',
     '%pages/crawl': '0.0138'},
]


def test_parse_csv() -> None:
    parsed = parse_csv(sample)
    assert isinstance(parsed[0]['urls'], int)
    assert isinstance(parsed[0]['pct_pages_per_crawl'],  float)
