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

def main(config: Config):
    crawl_cfg = config['data']['common_crawl']

    # Get the pre-aggregated statistics from the Common Crawl repository
    response = urlopen(crawl_cfg['stats_url'])
    lines = [line.decode('utf-8') for line in response.readlines()]
    contents = csv.DictReader(lines)
    stats = [line for line in contents]

    typed_stats = parse_csv(stats)
    declining = filter_declining(typed_stats)
    analyse(declining)

    print(stats)


if __name__ == '__main__':
    start = datetime.datetime.now()
    parser = ArgumentParser('Performs the Common Crawl MIME type usage-over-time analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    main(config)
    logging.info(f'Took {datetime.datetime.now() - start}')
