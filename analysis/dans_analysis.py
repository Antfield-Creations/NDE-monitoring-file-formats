import json
import logging
from argparse import ArgumentParser
from typing import List, Tuple

import numpy as np

from analysis.config import Config, load_config
from analysis.shared_parsers import PeriodicFiletypeCount, plot_counts, to_sorted_yearly, SortedFileCount


def main(config: Config) -> int:
    dans_cfg = config['data']['dans']

    with open(dans_cfg['filetype_monthly_aggregate_path'], 'rt') as f:
        monthly_stats: PeriodicFiletypeCount = json.loads(f.read())

    filecount_sum = 0
    for counts in monthly_stats.values():
        filecount_sum += sum(counts.values())

    logging.info(f'Total file count: {filecount_sum}')
    logging.info(f'DANS analysis has {len(monthly_stats.keys())} file types (reverse-sorted by count):')

    filetype_counts: List[Tuple[str, int]] = []
    for filetype, monthly_counts in monthly_stats.items():
        filetype_counts.append((filetype, sum(monthly_counts.values())))

    for (filetype, counts_for_type) in sorted(filetype_counts, key=lambda x: x[1], reverse=True):
        logging.info(f'{filetype} has a total of {counts_for_type} files')

    # Aggregate to counts per year
    yearly_stats = to_sorted_yearly(monthly_stats)

    # Keep only file types with more than the configured number of measurements and which are part of the selection
    keep_filetypes = filter_stats(yearly_stats, dans_cfg)

    logging.info(f'Keeping {len(keep_filetypes)} filetypes for analysis: {keep_filetypes}')
    kept_counts = {filetype: counts for filetype, counts in yearly_stats.items() if filetype in keep_filetypes}
    plot_counts(kept_counts, dans_cfg)

    return 0


def filter_stats(yearly_stats: SortedFileCount, dans_cfg: dict) -> List[str]:
    keep_filetypes: List[str] = []
    for filetype, yearly_counts in yearly_stats.items():
        # We do the exercise below because the mime types included in the "mime_plots" list was decided based on the
        # filters below
        if filetype not in dans_cfg['mime_plots']:
            continue

        counts_reversed = list(reversed(yearly_counts))
        if len(counts_reversed) == 0:
            continue

        # prune 0-counts
        while counts_reversed[0]['count'] == 0:
            counts_reversed.pop(0)

        if len(counts_reversed) < dans_cfg['minimum_time_periods']:
            continue

        # Take the last quarters to assess if the file type was in decline
        maybe_declining_period = yearly_counts[-dans_cfg['decline_periods']:]
        yearly_changes = np.diff([p['count'] for p in maybe_declining_period])

        # Ignore the file types with stable or increasing number quarterly_changes
        if yearly_changes.mean() >= 0:
            continue

        count_idx = 0
        while count_idx < len(yearly_counts):
            year = int(yearly_counts[count_idx]['period'][:5])
            if year < dans_cfg['min_year']:
                yearly_counts.pop(count_idx)
            else:
                count_idx += 1

        # Keep the rest
        keep_filetypes.append(filetype)

    return keep_filetypes


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Data Archiving and Networked Services file metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
