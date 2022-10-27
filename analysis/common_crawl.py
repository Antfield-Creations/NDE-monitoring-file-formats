import csv
import datetime
import json
import logging
import urllib.parse
from argparse import ArgumentParser
from typing import Dict, List, TypedDict
from urllib.request import urlopen

import numpy as np
from matplotlib import pyplot as plt
from numpy.lib.stride_tricks import sliding_window_view

from analysis.config import load_config, Config
from models.bass_diffusion import BassDiffusionModel

StatsDict = TypedDict('StatsDict',
                      {'crawl': str, 'mimetype_detected': str, 'pages': int, 'urls': int, 'pct_pages_per_crawl': float})
StatsDictTable = List[StatsDict]

Crawl, PageCount = str, int
MimeStats = Dict[str, int]
MimeType = str
MimeDict = Dict[MimeType, List[MimeStats]]

ModelStats = List[Dict[str, Union[str, float]]]


def main(config: Config) -> int:
    start = datetime.datetime.now()

    crawl_cfg = config['data']['common_crawl']

    # Get the collection metadata
    with urlopen(crawl_cfg['collection_url']) as f:
        coll_info = json.loads(f.read().decode('utf-8'))

    # Get the pre-aggregated statistics from the Common Crawl repository
    response = urlopen(crawl_cfg['stats_url'])
    lines = [line.decode('utf-8') for line in response.readlines()]
    contents = csv.DictReader(lines)
    stats = [line for line in contents]

    typed_stats = parse_csv(stats)
    declining = filter_declining(typed_stats)
    model_stats = analyse(declining, coll_info, config)
    logging.info(json.dumps(model_stats, indent=2))

    logging.info(f'Script took {datetime.datetime.now() - start}')
    return 0


def parse_csv(stats: List[Dict[str, str]]) -> StatsDictTable:
    """
    Converts str dict values to types appropriate for the StatsDictTable format.

    :param stats: A list of raw Common Crawl statistics csv values from a csv.DictReader

    :return: A list of dictionaries with parsed string, int and float values
    """
    stats_dict = []
    for row in stats:
        stats_dict.append(StatsDict(
            crawl=str(row['crawl']),
            mimetype_detected=str(row['mimetype_detected']),
            pages=int(row['pages']),
            urls=int(row['urls']),
            pct_pages_per_crawl=float(row['%pages/crawl']),
        ))

    return stats_dict


def filter_declining(typed_stats: StatsDictTable) -> MimeDict:
    """
    Filters the list of statistics for MIME types that decline over the last year

    :param typed_stats: a list of dictionaries with typed values

    :return: a dictionary of mime types with declining counts, with usage
    """
    declining_mime_types: dict = {}

    # First: "de-normalize" the table into a nested dictionary of mime types with page counts per crawl
    # This is easier to handle: we want to analyse statistics per mime type, over the years
    mime_sorted_stats = sorted(typed_stats, key=lambda r: (r['mimetype_detected'], r['crawl']))
    # Skip under-specified mime types
    mime_sorted_stats = [row for row in mime_sorted_stats
                         if row['mimetype_detected'] != '<unknown>' and row['mimetype_detected'] != '<other>']

    for row in mime_sorted_stats:
        declining_mime_types.setdefault(row['mimetype_detected'], [])
        usage_stat_ = str(config['data']['common_crawl']['usage_stat'])
        declining_mime_types[row['mimetype_detected']].append(
            {row['crawl']: row[usage_stat_]}  # type: ignore
        )

    mime_types = list(declining_mime_types.keys())
    mime_declines = []

    for mime_type in mime_types:
        crawl_stats = declining_mime_types[mime_type]
        # Calculate window averages of three crawls over the crawl stats
        stats_values = [list(stat.values())[0] for stat in crawl_stats]
        windows = sliding_window_view(stats_values, 3)
        window_averages = [np.mean(window) for window in windows]

        # Drop zero-values from mime types that are no longer used
        while window_averages[-1] == 0.:
            window_averages.pop()

        num_crawls = 12
        last_usage_percentages = window_averages[-num_crawls:]
        diffs = [pct[1] - pct[0] for pct in sliding_window_view(last_usage_percentages, 2)]
        avg_increase = np.mean(diffs)

        # Now that we have fitted a simple regression line, the filter is simple: a positive coefficient means growth,
        # a negative number indicates decline
        if avg_increase >= 0:
            del declining_mime_types[mime_type]
        else:
            mime_declines.append({'mime_type': mime_type, 'avg_increase': avg_increase})

    mime_declines = sorted(mime_declines, key=lambda x: x['avg_increase'])
    logging.info(f'Largest declines: {json.dumps(mime_declines[0:10], indent=2)}')

    return declining_mime_types


def extract_years(collection_metadata: List[Dict[str, str]]) -> List[str]:
    year_labels = []

    for crawl in reversed(collection_metadata):
        year = crawl['id'].split('-')[2]
        if year not in year_labels:
            year_labels.append(year)
        else:
            year_labels.append('')

    year_labels[0] = ''

    return year_labels


def analyse(stats: MimeDict, collection_metadata: List[Dict[str, str]], config: Config) -> ModelStats:
    error_stats: ModelStats = []
    # Extract out shorthand for long dict value
    cc_cfg = config['data']['common_crawl']

    x_axis_labels = extract_years(collection_metadata)

    for mime_type, usage_values in stats.items():
        usage_per_crawl = [list(row.values())[0] for row in usage_values]
        year_labels = x_axis_labels[-len(usage_per_crawl):]

        # Extract out the index for the test crawls
        test_crawls_idx = -cc_cfg['num_test_crawls']
        train_values = usage_per_crawl[:test_crawls_idx]

        all_times = np.array(range(len(usage_per_crawl)))
        train_times = all_times[:test_crawls_idx]
        test_times = all_times[test_crawls_idx:]

        # Fit the Bass model
        model = BassDiffusionModel()
        model.fit(times=train_times, sales=np.array(train_values))

        # Project Bass model "sales"
        fitted_data = model.sales_at_time(model.bass_parameters, train_times)
        projected_data = model.sales_at_time(model.bass_parameters, test_times)

        linear_model = LinearRegression()
        linear_model.fit(X=linear_train_times, y=linear_train_values)
        linear_fitted_values = linear_model.predict(linear_train_times)
        linear_projected_values = linear_model.predict(linear_test_times)

        # Calculate accuracy in average error
        actual_test_values = list(usage_per_crawl[:test_crawls_idx])
        assert type(actual_test_values) == list
        assert type(bass_projected_values) == list

        bass_error = [abs(actual - predicted) for actual, predicted
                      in zip(actual_test_values, bass_projected_values)]
        linear_error = [abs(actual - predicted) for actual, predicted
                        in zip(actual_test_values, linear_projected_values)]

        error_stats.append({
            'mime_type': mime_type,
            'bass_avg_test_error': mean(bass_error),
            'linear_avg_test_error': mean(linear_error)
        })

        # Plot if marked so in configuration
        if mime_type in cc_cfg['mime_plots']:
            plt.plot(
                # Actual values
                all_times, usage_per_crawl,
                # Model projections from data that the model has seen
                train_times, fitted_data,
                # Model projections from data that the model has not seen
                test_times, projected_data
            )
            plt.xticks(all_times, year_labels)
            plt.title(f"Common Crawl {cc_cfg['usage_stat']} per crawl voor {mime_type}")
            plt.legend([cc_cfg['usage_stat'].capitalize(), "Bass model", "Bass test"])
            plt.savefig(f'images/{urllib.parse.quote_plus(mime_type)}.png')
            plt.show()


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Common Crawl MIME type usage-over-time analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
