import json
from argparse import ArgumentParser

from analysis.config import load_config, Config


def main(config: Config):
    with open(config['data']['common-crawl']['index-file'], 'rt') as f:
        cc_roots = json.loads(f.read())


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Common Crawl MIME type usage over time analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    main(config)
