from analysis.common_crawl import extract_years


def test_something() -> None:
    test_data = [
        {"id": "CC-MAIN-2016-14", "name": "March 2015 Index",
         "timegate": "https://index.commoncrawl.org/CC-MAIN-2015-14/",
         "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2015-14-index"},
        {"id": "CC-MAIN-2015-11", "name": "February 2015 Index",
         "timegate": "https://index.commoncrawl.org/CC-MAIN-2015-11/",
         "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2015-11-index"},
        {"id": "CC-MAIN-2015-06", "name": "January 2015 Index",
         "timegate": "https://index.commoncrawl.org/CC-MAIN-2015-06/",
         "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2015-06-index"},
        {"id": "CC-MAIN-2014-52", "name": "December 2014 Index",
         "timegate": "https://index.commoncrawl.org/CC-MAIN-2014-52/",
         "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2014-52-index"},
        {"id": "CC-MAIN-2014-49", "name": "November 2014 Index",
         "timegate": "https://index.commoncrawl.org/CC-MAIN-2014-49/",
         "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2014-49-index"},
        {"id": "CC-MAIN-2014-42", "name": "October 2014 Index",
         "timegate": "https://index.commoncrawl.org/CC-MAIN-2014-42/",
         "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2014-42-index"}
    ]

    year_labels = extract_years(test_data)
    assert len(year_labels) == len(test_data)
    assert year_labels == ['', '', '', '2015', '', '2016']
