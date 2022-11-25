from analysis.shared_parsers import to_sorted_yearly


def test_year_aggregator() -> None:
    test_data = {
        'some_mime_type': {
            '2018-01': 100,
            '2018-02': 200,
            '2020-01': 300,
        }
    }
    yearly_stats = to_sorted_yearly(test_data)
    assert yearly_stats == {
        'some_mime_type': [
            {'period': '2018', 'count': 300},
            {'period': '2019', 'count': 0},
            {'period': '2020', 'count': 300},
            {'period': '2021', 'count': 0},
        ]
    }
