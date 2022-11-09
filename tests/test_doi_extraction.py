from analysis.scrape_dans import extract_dois


def test_doi_extraction() -> None:
    with open('tests/data/dans_page_data.html', 'rt') as f:
        dois = extract_dois(f.read())

    assert len(dois) == 10
    for doi in dois:
        assert doi.startswith('doi:')
