import datetime
import gzip
import json
import logging
from argparse import ArgumentParser
from collections import Counter

from analysis.config import load_config, Config


def main(config: Config):
    crawl_cfg = config['data']['common_crawl']
    with open(crawl_cfg['index_file'], 'rt') as f:
        cc_roots = json.loads(f.read())

        for root in cc_roots:
            if root['id'] < config['data']['common_crawl']['start_from']:
                continue

            logging.info(f'Analysing {root["name"]}')
            analysis = analyse(root['name'], )


def analyse(root_url: str) -> Counter:
    return Counter()


if __name__ == '__main__':
    start = datetime.datetime.now()
    parser = ArgumentParser('Performs the Common Crawl MIME type usage over time analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    main(config)
    logging.info(f'Took {datetime.datetime.now() - start}')
