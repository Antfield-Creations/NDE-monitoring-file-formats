from analysis.config import load_config
from analysis.scrape_dans import parse_page


def test_doi_extraction(self):
    config = load_config()
    dans_cfg = config['data']['dans']

    with open('tests/data/dans_page_data.html', 'rt') as f:
        dois = parse_page(f.read(), dans_cfg)

    assert len(dois) == 10
