import datetime
import json
import logging
import os
from argparse import ArgumentParser

from analysis.config import load_config, Config


quarter_mapping = {
    '-01': "Q1",
    '-02': "Q1",
    '-03': "Q1",
    '-04': "Q2",
    '-05': "Q2",
    '-06': "Q2",
    '-07': "Q3",
    '-08': "Q3",
    '-09': "Q3",
    '-10': "Q4",
    '-11': "Q4",
    '-12': "Q4",
}


def main(config: Config) -> int:
    start = datetime.datetime.now()
    nibg_cfg = config['data']['nibg']

    aggregate_stats_path = os.path.join(nibg_cfg['json_output_dir'], 'nibg_aggregate_stats.json')
    with open(aggregate_stats_path, 'rt') as f:
        aggregate_stats = json.loads(f.read())

        for format_name, stats in aggregate_stats.items():
            periods = list(stats.keys())
            counts = list(stats.items())

            pass

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid file archive metadata aggregation')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
