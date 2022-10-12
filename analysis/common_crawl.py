import datetime
import logging
from argparse import ArgumentParser
from typing import Dict, List, TypedDict
from urllib.request import urlopen

from analysis.config import load_config, Config


def main(config: Config):
    crawl_cfg = config['data']['common_crawl']

    with urllib.request.urlopen(crawl_cfg['stats_url']) as f:
        stats = f.read()

    print(stats)


if __name__ == '__main__':
    start = datetime.datetime.now()
    parser = ArgumentParser('Performs the Common Crawl MIME type usage-over-time analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    main(config)
    logging.info(f'Took {datetime.datetime.now() - start}')
