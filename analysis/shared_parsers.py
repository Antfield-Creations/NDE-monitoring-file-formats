from typing import List


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

