from analysis.shared_parsers import SortedFileCount, add_cumulative_counts


def test_cumulative() -> None:
    test_data: SortedFileCount = {
        '.jpg': [
            {'period': '2017', 'count': 1},
            {'period': '2018', 'count': 2},
            {'period': '2019', 'count': 3},
        ]
    }

    cum_period_counts = add_cumulative_counts(test_data, '.jpg')
    assert '.jpg cumulative' in cum_period_counts.keys()
    abs_counts = [period_count['count'] for period_count in test_data['.jpg']]
    cum_counts = [period_count['count'] for period_count in cum_period_counts['.jpg cumulative']]
    assert cum_counts[-1] == sum(abs_counts)
