import datetime
import json
import logging
import math
import os
from argparse import ArgumentParser
from typing import Dict, List

from analysis.config import load_config, Config

Filetype = str
PeriodicFiletypeCount = Dict[Filetype, Dict[str, int]]
SortedFileCount = Dict[Filetype, List[Dict[str, int]]]


def main(config: Config) -> int:
    start = datetime.datetime.now()
    nibg_cfg = config['data']['nibg']

    aggregate_stats_path = os.path.join(nibg_cfg['json_output_dir'], 'nibg_aggregate_stats.json')
    with open(aggregate_stats_path, 'rt') as f:
        aggregate_stats = json.loads(f.read())

    quarterly_counts = to_sorted_quarterly(aggregate_stats)
    logging.info(f'{quarterly_counts=}')

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


def to_sorted_quarterly(file_type_montly_counts: PeriodicFiletypeCount) -> SortedFileCount:
    quarterly_counts: SortedFileCount = {}

    for file_type, monthly_counts in file_type_montly_counts.items():
        quarterly_counts.setdefault(file_type, [])

        time_sorted = list(monthly_counts.items())
        time_sorted = sorted(time_sorted, key=lambda stats: stats[0])

        for year_month, count in time_sorted:
            year = year_month.split('-')[0]
            month = int(year_month.split('-')[1])
            quarter = math.ceil(month / 4)
            this_quarter = f'{year}Q{quarter}'

            type_counts = quarterly_counts[file_type]
            if len(type_counts) == 0:
                type_counts.append({this_quarter: 0})

            latest_quarter, latest_count = list(type_counts[-1].items())[-1]
            if latest_quarter == this_quarter:
                type_counts[-1][this_quarter] += count
            else:
                type_counts.append({this_quarter: count})

        return quarterly_counts


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
