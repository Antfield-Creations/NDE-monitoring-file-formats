import csv
import datetime
import logging
from argparse import ArgumentParser
from typing import Dict, List, TypedDict
from urllib.request import urlopen

from analysis.config import load_config, Config

StatsDict = TypedDict('StatsDict',
                      {'crawl': str, 'mimetype_detected': str, 'pages': int, 'urls': int, 'pct_pages_per_crawl': float})
StatsDictTable = List[StatsDict]

Crawl, PageCount = str, int
MimeStats = Dict[Crawl, PageCount]
MimeType = str
MimeDict = Dict[MimeType, MimeStats]


def main(config: Config) -> None:
    crawl_cfg = config['data']['common_crawl']

    # Get the pre-aggregated statistics from the Common Crawl repository
    response = urlopen(crawl_cfg['stats_url'])
    lines = [line.decode('utf-8') for line in response.readlines()]
    contents = csv.DictReader(lines)
    stats = [line for line in contents]

    typed_stats = parse_csv(stats)
    declining = filter_declining(typed_stats)
    analyse(declining)


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
    declining_mime_types = {}

    # First: "de-normalize" the table into a nested dictionary of mime types with page counts per crawl
    # This is easier to handle: we want to analyse statistics per mime type, over the years
    mime_types = set([stat['mimetype_detected'] for stat in typed_stats])
    for row in typed_stats:
        declining_mime_types.setdefault(row['mimetype_detected'], 0)
        declining_mime_types[row['mimetype_detected']] += row['pages']

    return declining_mime_types


def analyse(stats: MimeDict) -> None:
    pass


if __name__ == '__main__':
    start = datetime.datetime.now()
    parser = ArgumentParser('Performs the Common Crawl MIME type usage-over-time analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    main(config)
    logging.info(f'Took {datetime.datetime.now() - start}')
