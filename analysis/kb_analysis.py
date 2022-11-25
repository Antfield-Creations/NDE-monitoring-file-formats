import datetime
import json
import logging
import math
import os
from argparse import ArgumentParser
from typing import Dict, List, TypedDict

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

from analysis.config import load_config, Config
from analysis.shared_parsers import extract_year_ticks, next_year_quarter
from models.bass_diffusion import BassDiffusionModel

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


def to_sorted_quarterly(file_type_montly_counts: PeriodicFiletypeCount) -> SortedFileCount:
    quarterly_counts: SortedFileCount = {}

    for file_type, monthly_counts in file_type_montly_counts.items():
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
            if year > current_year:
                logging.warning(f'Expected year entry not to be in the future, got {year}, skipping')
                continue

            month = int(year_month.split('-')[0])
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

        quarter = math.ceil(datetime.datetime.now().month / 3)
        current_quarter = f'{datetime.datetime.now().year}Q{quarter}'
        
        while quarterly_counts[file_type][-1]['period'] != current_quarter:
            last_measured = quarterly_counts[file_type][-1]['period']
            next_year, next_quarter = next_year_quarter(last_measured)
            quarterly_counts[file_type].append({
                'period': f'{next_year}Q{next_quarter}', 'count': 0
            })

        # Chop off the current quarter: counts may still be incomplete
        quarterly_counts[file_type].pop(-1)

    return quarterly_counts


def plot_counts(counts: SortedFileCount, kb_cfg: dict) -> None:
    output_dir = kb_cfg['img_output_dir']
    num_tests = kb_cfg['num_test_measurements']

    for file_type, quarter_counts in counts.items():
        quarters = [entry['period'] for entry in quarter_counts]

        # Set up training and test data
        all_times = list(range(len(quarters)))
        train_times = all_times[:-num_tests]
        test_times = all_times[-num_tests:]

        all_counts = [entry['count'] for entry in quarter_counts]
        train_counts = all_counts[:-num_tests]
        # test_counts = all_counts[-num_tests:]

        # Fit the Bass model and produce data
        bass_model = BassDiffusionModel()
        train_inputs = np.array(train_times)
        test_inputs = np.array(test_times)
        bass_model.fit(train_inputs, np.array(train_counts))
        fitted_values = bass_model.sales_at_time(bass_model.bass_parameters, train_inputs)
        projected_values = bass_model.sales_at_time(bass_model.bass_parameters, test_inputs)

        plot_data = [
            all_times, all_counts,
            train_times, fitted_values,
            test_times, projected_values
        ]
        legend_data = [
            'Aantal bestanden',
            'Bass "fit"',
            'Bass "test"'
        ]

        if file_type in kb_cfg['linear_plots']:
            # Fit linear model for selected file formats
            linear_model = LinearRegression()
            max_idx = train_counts.index(max(train_counts))
            linear_train_times = np.expand_dims(all_times[max_idx:-num_tests], 1)
            linear_train_counts = all_counts[max_idx:-num_tests]
            linear_test_times = np.expand_dims(all_times[-num_tests:], 1)

            linear_model.fit(linear_train_times, linear_train_counts)
            linear_fitted_values = linear_model.predict(linear_train_times)
            linear_projected_values = linear_model.predict(linear_test_times)

            plot_data.extend([linear_train_times, linear_fitted_values])
            plot_data.extend([linear_test_times, linear_projected_values])
            legend_data.append('Lineair "fit"')
            legend_data.append('Lineair "test"')

        plt.plot(*plot_data)
        x_axis_labels = extract_year_ticks(quarters, separator='Q', index=0)
        plt.title(f"KB tellingen voor bestandstype {file_type}")
        plt.xticks(all_times, x_axis_labels, rotation=45)
        plt.legend(legend_data)
        plt.savefig(os.path.join(output_dir, f'{file_type}.png'))
        plt.show()


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
