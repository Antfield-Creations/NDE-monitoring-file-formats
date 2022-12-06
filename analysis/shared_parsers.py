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


def all_filetype_counts(periodic_stats: SortedFileCount) -> SortedFileCount:
    """
    Aggregates a SortedFileCount from all file types to a single file type named 'all', to calculate a complete count
    over all file types. This helps in establishing a view on the overall deposited data in a digital archive.

    :param periodic_stats: A SortedFileCount with counts per period, per file type

    :return: A SortedFileCount with all counts per period combined into a single "virtual" file type named 'all'.
    """
    periodic_combined: SortedFileCount = {'all': []}
    for period_counts in periodic_stats.values():
        for period_count in period_counts:
            # Add a new period entry if it isn't listed yet
            already_periods = {count['period']: idx for idx, count in enumerate(periodic_combined['all'])}
            if period_count['period'] not in already_periods.keys():
                periodic_combined['all'].append({'period': period_count['period'], 'count': 0})
                # Update the available periods that have already been added
                already_periods = {count['period']: idx for idx, count in enumerate(periodic_combined['all'])}

            # Update the counts for an already listed period
            period_idx = already_periods[period_count['period']]
            periodic_combined['all'][period_idx]['count'] += period_count['count']

    # Now, the list has become unsorted because we iterated over all file types first, so we sort again
    periodic_combined['all'] = sorted(periodic_combined['all'], key=lambda counts: counts['period'])

    return periodic_combined


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


def to_pruned_sorted_quarterly(filetype_monthly_counts: PeriodicFiletypeCount) -> SortedFileCount:
    quarterly_counts: SortedFileCount = {}

    current_quarter = math.ceil(datetime.datetime.now().month / 3)
    current_year = datetime.datetime.now().year
    current_year_quarter = f'{current_year}Q{current_quarter}'

    for file_type, monthly_counts in filetype_monthly_counts.items():
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


def to_sorted_yearly(filetype_monthly_counts: PeriodicFiletypeCount) -> SortedFileCount:
    """
    Helper function to build a list of sorted yearly counts, based on monthly counts per file type

    :param filetype_monthly_counts: A dictionary with file types and counts per month as values

    :return: A dictionary of file types as keys and a sorted list of years and  corresponding summed counts
    """
    current_year = datetime.datetime.now().year
    year_counts: SortedFileCount = {}

    for file_type, monthly_counts in filetype_monthly_counts.items():
        year_counts.setdefault(file_type, [])

        time_sorted = list(monthly_counts.items())
        time_sorted = sorted(time_sorted, key=lambda stats: stats[0])

        for year_month, count in time_sorted:
            if re.match(pattern=r'\d{4}-\d{2}', string=year_month) is None:
                logging.warning(f'Expected year-month formatted YYYY-mm, got {year_month}, skipping')
                continue

            year = year_month.split('-')[0]
            if int(year) > current_year:
                logging.warning(f'Expected year entry not to be in the future, got {year}, skipping')
                continue

            type_counts = year_counts[file_type]
            # Initialize a first count for the file type if the list of counts is empty
            if len(type_counts) == 0:
                type_counts.append({'period': year, 'count': 0})

            last_period = type_counts[-1]['period']
            # Autofill zero-count in-between periods: append zero counts for all missing periods until latest year
            while type_counts[-1]['period'] != str(year):
                type_counts.append({'period': str(int(type_counts[-1]['period']) + 1), 'count': 0})

            # Add this month's count to the quarterly counts if the quarter is already there
            type_counts[-1]['count'] += count

        # Autofill zero-count periods after the last one if the last period isn't the current year
        while year_counts[file_type][-1]['period'] != str(current_year):
            last_period = year_counts[file_type][-1]['period']
            year_counts[file_type].append({
                'period': str(int(last_period) + 1), 'count': 0
            })

        # Chop off the current quarter: counts may still be incomplete
        year_counts[file_type].pop(-1)

    return year_counts


def add_cumulative_counts(counts: SortedFileCount, format: str) -> SortedFileCount:
    """
    Produces a cumulative count for specified `format`, under the key '{`format`} cumulative'

    :param counts:  A dictionary of file formats with each a list of period-sorted counts
    :param format:  The format to produce cumulative counts for

    :return: The same SortedFileCount with an added "{format} cumulative" key with cumulative counts
    """
    if format not in counts:
        raise KeyError(f'Given key {format} not found in {counts.keys()}')

    abs_counts = [period_count['count'] for period_count in counts[format]]
    periods = [period_count['period'] for period_count in counts[format]]
    cum_counts = np.cumsum(abs_counts)
    counts[f'{format} cumulatief'] = []

    for period, cum_count in zip(periods, cum_counts):
        counts[f'{format} cumulatief'].append({'period': period, 'count': cum_count})

    return counts


def plot_counts(counts: SortedFileCount, cfg: dict) -> None:
    output_dir = cfg['img_output_dir']
    num_tests = cfg['num_test_measurements']

    for filetype, period_counts in counts.items():
        periods = [entry['period'] for entry in period_counts]

        all_times = list(range(len(periods)))
        all_counts = [entry['count'] for entry in period_counts]

        train_counts = all_counts[:-num_tests]

        plot_data = [
            all_times, all_counts,
        ]
        legend_data = [
            'Aantal bestanden',
        ]

        # Set up training and test data
        train_times = all_times[:-num_tests]
        test_times = all_times[-num_tests:]

        train_inputs = np.array(train_times)
        test_inputs = np.array(test_times)

        bass_model = BassDiffusionModel()

        if filetype.endswith('cumulatief'):
            train_counts.insert(0, 0)
            train_counts = np.diff(train_counts)
            predict = bass_model.predict_cumulative
        else:
            predict = bass_model.predict

        # Fit the Bass model and produce data
        try:
            bass_model.fit(train_inputs, np.array(train_counts))
        except RuntimeError as e:
            logging.error(f'Unable to fit Bass model based on train inputs {train_counts}: {e}')
            continue

        fitted_values = predict(train_inputs)
        projected_values = predict(test_inputs)

        plot_data.extend([
            # Type-force the values to list to ensure compatibility with plot_data
            train_times, np.array(fitted_values).tolist(),
            test_times, np.array(projected_values).tolist(),
            ])
        legend_data.extend([
            'Bass "fit"',
            'Bass "test"'
        ])

        if filetype in cfg['linear_plots']:
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
        x_axis_labels = extract_year_ticks(periods, separator='Q', index=0)
        plt.title(f"Tellingen per periode voor bestandstype {filetype}")
        plt.xticks(all_times, x_axis_labels, rotation=45)
        plt.legend(legend_data)

        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(os.path.join(output_dir, f'{quote_plus(filetype)}.png'))
        plt.show()
