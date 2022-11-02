from analysis.scrape_dans import parse_page


def test_doi_extraction():
    with open('tests/data/dans_page_data.html', 'rt') as f:
        dois = parse_page(f.read())

    assert len(dois) == 10
    for doi in dois:
        assert doi.startswith('doi:')
