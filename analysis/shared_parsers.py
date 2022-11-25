import datetime
import logging
import math
import os
import re
from typing import List, Tuple, Dict, TypedDict
from urllib.parse import quote_plus

import numpy as np
from matplotlib import pyplot as plt
from sklearn.linear_model import LinearRegression

from models import BassDiffusionModel


class PeriodCount(TypedDict):
    """
    Simple data structure for periods as strings with counts in whole positive numbers
    """
    period: str
    count: int


# Type aliases
Filetype = str
PeriodicFiletypeCount = Dict[Filetype, Dict[str, int]]
SortedFileCount = Dict[Filetype, List[PeriodCount]]


def extract_year_ticks(time_labels: List[str], separator: str = '-', index: int = 2) -> List[str]:
    year_labels = []

    for label in time_labels:
        year = label.split(separator)[index]
        if year not in year_labels:
            year_labels.append(year)
        else:
            year_labels.append('')

    year_labels[0] = ''

    return year_labels


def next_year_quarter(last_period: str) -> Tuple[int, int]:
    """
    A small helper function to calculate the next quarter.

    :param last_period: The quarter to calculate the next one for

    :return: a tuple of the year (perhaps next year) and the next quarter
    """
    last_measured_year = int(last_period.split('Q')[0])
    last_measured_quarter = int(last_period.split('Q')[1])
    next_quarter = last_measured_quarter + 1 if last_measured_quarter < 4 else 1
    year = last_measured_year if next_quarter > 1 else last_measured_year + 1

    return year, next_quarter


def to_pruned_sorted_quarterly(file_type_montly_counts: PeriodicFiletypeCount) -> SortedFileCount:
    quarterly_counts: SortedFileCount = {}

    current_quarter = math.ceil(datetime.datetime.now().month / 3)
    current_year = datetime.datetime.now().year
    current_year_quarter = f'{current_year}Q{current_quarter}'

    for file_type, monthly_counts in file_type_montly_counts.items():
        quarterly_counts.setdefault(file_type, [])

        time_sorted = list(monthly_counts.items())
        time_sorted = sorted(time_sorted, key=lambda stats: stats[0])

        for year_month, count in time_sorted:
            if re.match(pattern=r'\d{4}-\d{2}', string=year_month) is None:
                logging.warning(f'Expected year-month formatted YYYY-mm, got {year_month}, skipping')
                continue

            year = int(year_month.split('-')[0])
            if year > current_year:
                logging.warning(f'Expected year entry not to be in the future, got {year}, skipping')
                continue

            month = int(year_month.split('-')[1])
            quarter = math.ceil(month / 3)
            year_quarter = f'{year}Q{quarter}'

            type_counts = quarterly_counts[file_type]
            # Initialize a first count for the file type if it's empty
            if len(type_counts) == 0:
                type_counts.append({'period': year_quarter, 'count': 0})

            latest_quarter = type_counts[-1]['period']
            if latest_quarter == year_quarter:
                # Add this month's count to the quarterly counts if the quarter is already there
                type_counts[-1]['count'] += count
            else:
                # Autofill zero-count in-between quarters
                while type_counts[-1]['period'] != year_quarter:
                    last_period = type_counts[-1]['period']
                    next_year, next_quarter = next_year_quarter(last_period)
                    type_counts.append({'period': f'{next_year}Q{next_quarter}', 'count': 0})

                # Add the new count
                type_counts[-1]['count'] += count

        last_period = quarterly_counts[file_type][-1]['period']
        while last_period != current_year_quarter:
            last_period = quarterly_counts[file_type][-1]['period']
            next_year, next_quarter = next_year_quarter(last_period)
            quarterly_counts[file_type].append({
                'period': f'{next_year}Q{next_quarter}', 'count': 0
            })

        # Chop off the current quarter: counts may still be incomplete
        quarterly_counts[file_type].pop(-1)

    return quarterly_counts


def plot_counts(counts: SortedFileCount, cfg: dict) -> None:
    output_dir = cfg['img_output_dir']
    num_tests = cfg['num_test_measurements']

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

        if file_type in cfg['linear_plots']:
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
        plt.title(f"NIBG tellingen voor bestandstype {file_type}")
        plt.xticks(all_times, x_axis_labels, rotation=45)
        plt.legend(legend_data)
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(os.path.join(output_dir, f'{quote_plus(file_type)}.png'))
        plt.show()
