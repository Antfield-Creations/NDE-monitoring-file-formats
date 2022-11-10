import datetime
import json
import logging
import math
import os
from argparse import ArgumentParser
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

from analysis.config import load_config, Config
from analysis.shared_parsers import extract_year_ticks
from models.bass_diffusion import BassDiffusionModel

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
    plot_counts(quarterly_counts)

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


def plot_counts(counts: SortedFileCount) -> None:
    for file_type, quarter_counts in counts.items():
        quarters = [list(entry.keys())[0] for entry in quarter_counts]
        file_counts = [list(entry.values())[0] for entry in quarter_counts]

        # Fit the Bass model
        times = list(range(len(file_counts)))
        bass_model = BassDiffusionModel()
        bass_model.fit(np.array(times), np.array(file_counts))

        plt.plot(
            times, file_counts
        )
        x_axis_labels = extract_year_ticks(quarters, separator='Q', index=0)
        plt.title(f"NIBG tellingen voor bestandstype {file_type}")
        plt.xticks(times, x_axis_labels, rotation=45)
        plt.legend(['Aantal bestanden'])
        plt.show()


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
