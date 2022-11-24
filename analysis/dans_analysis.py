import json
import logging
from argparse import ArgumentParser
from typing import List, Tuple

from analysis.config import Config, load_config
from analysis.shared_parsers import to_pruned_sorted_quarterly, PeriodicFiletypeCount


def main(config: Config) -> int:

    with open(config['data']['dans']['filetype_monthly_aggregate_path'], 'rt') as f:
        monthly_stats: PeriodicFiletypeCount = json.loads(f.read())

    filecount_sum = 0
    for counts in monthly_stats.values():
        filecount_sum += sum(counts.values())

    logging.info(f'Total file count: {filecount_sum}')

    logging.info(f'DANS analysis has {len(monthly_stats.keys())} file types (reverse-sorted by count:')

    filetype_counts: List[Tuple[str, int]] = []
    for filetype, monthly_counts in monthly_stats.items():
        filetype_counts.append((filetype, sum(monthly_counts.values())))

    for (filetype, counts_for_type) in sorted(filetype_counts, key=lambda x: x[1], reverse=True):
        logging.info(f'{filetype} has a total of {counts_for_type} files')

    quarterly_stats = to_pruned_sorted_quarterly(file_type_montly_counts=monthly_stats)
    logging.info(quarterly_stats)

    return 0


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Data Archiving and Networked Services file metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
