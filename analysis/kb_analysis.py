import math

import datetime
import json
import logging
import os
import re
from argparse import ArgumentParser
from typing import Dict, List, TypedDict

from analysis.config import load_config, Config
from analysis.shared_parsers import next_year_quarter, plot_counts

Filetype = str
PeriodicFiletypeCount = Dict[Filetype, Dict[str, int]]


class PeriodCount(TypedDict):
    period: str
    count: int


SortedFileCount = Dict[Filetype, List[PeriodCount]]


def main(config: Config) -> int:
    start = datetime.datetime.now()
    kb_cfg = config['data']['kb']

    aggregate_stats_path = os.path.join(kb_cfg['json_output_dir'], 'kb_aggregate_stats.json')
    with open(aggregate_stats_path, 'rt') as f:
        aggregate_stats = json.loads(f.read())

    quarterly_counts = to_sorted_quarterly(aggregate_stats)
    plot_counts(quarterly_counts, kb_cfg)

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


def to_sorted_quarterly(file_type_monthly_counts: PeriodicFiletypeCount) -> SortedFileCount:
    quarterly_counts: SortedFileCount = {}

    # hack for the KB data
    current_year = int(2014)

    for file_type, monthly_counts in file_type_monthly_counts.items():
        quarterly_counts.setdefault(file_type, [])

        time_sorted = list(monthly_counts.items())
        time_sorted = sorted(time_sorted, key=lambda stats: stats[0])

        for year_month, count in time_sorted:
            # Make sure the year/month string is properly formatted
            if re.match(pattern=r'\d{4}-\d{2}', string=year_month) is None:
                logging.warning(f'Expected year-month formatted YYYY-mm, got {year_month}, skipping')
                continue

            # Make sure that the year is not in the future, otherwise the autofill of intermediate
            # Missing 0-count periods until the current period end only until your memory runs out
            year = int(year_month.split('-')[0])
            print("year" + str(year))
            if year > current_year:
                logging.warning(f'Expected year entry not to be in the future, got {year}, skipping')
                continue

            month = int(year_month.split('-')[1])
            quarter = math.ceil(month / 3)
            this_quarter = f'{year}Q{quarter}'

            type_counts = quarterly_counts[file_type]
            print(type_counts)
            # Initialize a first count for the file type if it's empty
            if len(type_counts) == 0:
                type_counts.append({'period': this_quarter, 'count': 0})

            latest_quarter = type_counts[-1]['period']
            if latest_quarter == this_quarter:
                # Add this month's count to the quarterly counts if the quarter is already there
                type_counts[-1]['count'] += count
            else:
                # Autofill zero-count in-between quarters
                while type_counts[-1]['period'] != this_quarter:
                    last_period = type_counts[-1]['period']
                    next_year, next_quarter = next_year_quarter(last_period)
                    type_counts.append({'period': f'{next_year}Q{next_quarter}', 'count': 0})

                # Add the new count
                type_counts[-1]['count'] += count

        # hack for the KB data
        # quarter = math.ceil(datetime.datetime.now().month / 3)
        # current_quarter = f'{datetime.datetime.now().year}Q{quarter}'
        month_now = int(12)
        year_now = int(2014)
        quarter = math.ceil(month_now / 3)
        current_quarter = f'{year_now}Q{quarter}'

        while quarterly_counts[file_type][-1]['period'] != current_quarter:
            last_measured = quarterly_counts[file_type][-1]['period']
            next_year, next_quarter = next_year_quarter(last_measured)
            quarterly_counts[file_type].append({
                'period': f'{next_year}Q{next_quarter}', 'count': 0
            })

        # Chop off the current quarter: counts may still be incomplete
        quarterly_counts[file_type].pop(-1)

    return quarterly_counts


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
