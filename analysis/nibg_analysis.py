import datetime
import json
import logging
import os
from argparse import ArgumentParser

from analysis.config import load_config, Config


def main(config: Config) -> int:
    start = datetime.datetime.now()
    nibg_cfg = config['data']['nibg']

    aggregate_stats_path = os.path.join(nibg_cfg['json_output_dir'], 'nibg_aggregate_stats.json')
    with open(aggregate_stats_path, 'wt') as f:
        aggregate_stats = json.loads(f.read())

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid file archive metadata aggregation')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
