import datetime
import json
import logging
import math
import os
from argparse import ArgumentParser
from typing import Dict

from analysis.config import load_config, Config


def main(config: Config) -> int:
    start = datetime.datetime.now()
    nibg_cfg = config['data']['nibg']

    aggregate_stats_path = os.path.join(nibg_cfg['json_output_dir'], 'nibg_aggregate_stats.json')
    with open(aggregate_stats_path, 'rt') as f:
        aggregate_stats = json.loads(f.read())

    to_sorted_quarterly(aggregate_stats)

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


def to_sorted_quarterly(file_type_montly_counts: Dict[str, int]) -> Dict[str, int]:
    monthly_counts = list(file_type_montly_counts.items())
    monthly_counts = sorted(monthly_counts, key=lambda stats: stats[0])
    quarterly_counts: Dict[str, int] = {}

    for year_month, count in monthly_counts:
        year = year_month.split('-')[0]
        month = int(year_month.split('-')[1])
        quarter = math.ceil(month / 4)

        quarterly_counts.setdefault(f'{year}Q{quarter}', 0)
        quarterly_counts[f'{year}Q{quarter}'] += count

    return quarterly_counts


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
