import csv
import datetime
import json
import logging
from argparse import ArgumentParser
from typing import Dict, List, TypedDict
from urllib.request import urlopen

import numpy as np
from matplotlib import pyplot as plt
from numpy.lib.stride_tricks import sliding_window_view

from analysis.config import load_config, Config

StatsDict = TypedDict('StatsDict',
                      {'crawl': str, 'mimetype_detected': str, 'pages': int, 'urls': int, 'pct_pages_per_crawl': float})
StatsDictTable = List[StatsDict]

Crawl, PageCount = str, int
MimeStats = Dict[str, int]
MimeType = str
MimeDict = Dict[MimeType, MimeStats]


def main(config: Config) -> int:
    start = datetime.datetime.now()

    crawl_cfg = config['data']['common_crawl']

    # Get the pre-aggregated statistics from the Common Crawl repository
    response = urlopen(crawl_cfg['stats_url'])
    lines = [line.decode('utf-8') for line in response.readlines()]
    contents = csv.DictReader(lines)
    stats = [line for line in contents]

    typed_stats = parse_csv(stats)
    declining = filter_declining(typed_stats)
    analyse(declining, config)

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

    :return: a dictionary of mime types with declining counts, with the count per year
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
        declining_mime_types[row['mimetype_detected']].append({row['crawl']: row['pages']})

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
    logging.info('Declining mime types:')
    logging.info(declining_mime_types)

    return declining_mime_types


def analyse(stats: MimeDict, config: Config) -> None:
    for mime_type in config['data']['commom_crawl']['mime_plots']:
        values = [row.values() for row in stats[mime_type]]
        plt.plot(values)
        plt.title(mime_type)
        plt.legend(['Pages'])
        plt.show()


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Common Crawl MIME type usage-over-time analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
