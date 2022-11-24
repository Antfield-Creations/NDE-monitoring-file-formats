import datetime
import logging
import math
import re
from typing import List, Tuple, Dict, TypedDict


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
    A small helper function to calculate the next quarter

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
