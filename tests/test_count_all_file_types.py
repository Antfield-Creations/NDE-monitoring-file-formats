from analysis.shared_parsers import SortedFileCount, all_filetype_counts


def test_periodic_all_filetype_count_aggregation() -> None:
    test_data: SortedFileCount = {
        '.jpg': [
            {'period': '2018Q1', 'count': 1},
            {'period': '2018Q3', 'count': 3},
            {'period': '2018Q2', 'count': 2},
        ],
        '.tif': [
            {'period': '2019Q1', 'count': 1},
            {'period': '2017Q2', 'count': 3},
            {'period': '2018Q2', 'count': 2},
        ]
    }

    all_counts = all_filetype_counts(test_data)
    assert list(all_counts.keys()) == ['all']

    total_sum = sum(period_count['count'] for period_count in all_counts['all'])
    assert total_sum == 12

    # Assert that the list of periods is sorted by period
    all_periods = [period_count['period'] for period_count in all_counts['all']]
    assert all_periods == sorted(all_periods)
