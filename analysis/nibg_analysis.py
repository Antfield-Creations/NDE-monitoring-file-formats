import datetime
import json
import logging
import math
import os
from argparse import ArgumentParser
from typing import Dict, List, TypedDict

import matplotlib.pyplot as plt
import numpy as np

from analysis.config import load_config, Config
from analysis.shared_parsers import extract_year_ticks
from models.bass_diffusion import BassDiffusionModel

Filetype = str
PeriodicFiletypeCount = Dict[Filetype, Dict[str, int]]


class PeriodCount(TypedDict):
    period: str
    count: int


SortedFileCount = Dict[Filetype, List[PeriodCount]]


def main(config: Config) -> int:
    start = datetime.datetime.now()
    nibg_cfg = config['data']['nibg']

    aggregate_stats_path = os.path.join(nibg_cfg['json_output_dir'], 'nibg_aggregate_stats.json')
    with open(aggregate_stats_path, 'rt') as f:
        aggregate_stats = json.loads(f.read())

    quarterly_counts = to_sorted_quarterly(aggregate_stats)
    plot_counts(quarterly_counts, nibg_cfg)

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
            quarter = math.ceil(month / 3)
            this_quarter = f'{year}Q{quarter}'

            type_counts = quarterly_counts[file_type]
            if len(type_counts) == 0:
                type_counts.append({'period': this_quarter, 'count': 0})

            latest_quarter = type_counts[-1]['period']
            if latest_quarter == this_quarter:
                type_counts[-1]['count'] += count
            else:
                type_counts.append({'period': this_quarter, 'count': count})

    return quarterly_counts


def plot_counts(counts: SortedFileCount, nibg_cfg: dict) -> None:
    output_dir = nibg_cfg['img_output_dir']
    num_tests = nibg_cfg['num_test_measurements']

    for file_type, quarter_counts in counts.items():
        quarters = [entry['period'] for entry in quarter_counts]

        # Set up training and test data
        all_times = list(range(len(quarters)))
        train_times = all_times[:-num_tests]
        test_times = all_times[-num_tests:]

        all_counts = [entry['count'] for entry in quarter_counts]
        train_counts = all_counts[:-num_tests]
        # test_counts = all_counts[-num_tests:]

        # Fit the Bass model and data
        bass_model = BassDiffusionModel()
        train_inputs = np.array(train_times)
        test_inputs = np.array(test_times)
        bass_model.fit(train_inputs, np.array(train_counts))
        fitted_values = bass_model.sales_at_time(bass_model.bass_parameters, train_inputs)
        projected_values = bass_model.sales_at_time(bass_model.bass_parameters, test_inputs)

        plt.plot(
            all_times, all_counts,
            train_times, fitted_values,
            test_times, projected_values
        )
        x_axis_labels = extract_year_ticks(quarters, separator='Q', index=0)
        plt.title(f"NIBG tellingen voor bestandstype {file_type}")
        plt.xticks(all_times, x_axis_labels, rotation=45)
        plt.legend([
            'Aantal bestanden',
            'Bass "fit"',
            'Bass "test"'
        ])
        plt.show()
        plt.savefig(os.path.join(output_dir, f'{file_type}.png'))


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
