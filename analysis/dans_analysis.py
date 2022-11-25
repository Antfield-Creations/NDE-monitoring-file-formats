import json
import logging
from argparse import ArgumentParser
from typing import List, Tuple

import numpy as np

from analysis.config import Config, load_config
from analysis.shared_parsers import to_pruned_sorted_quarterly, PeriodicFiletypeCount, plot_counts


def main(config: Config) -> int:
    dans_cfg = config['data']['dans']

    with open(dans_cfg['filetype_monthly_aggregate_path'], 'rt') as f:
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

    # Keep only file types with more than the configured number of measurements and which are part of the selection
    keep_filetypes: List[str] = []
    for filetype, quarterly_counts in quarterly_stats.items():
        counts_reversed = list(reversed(quarterly_counts))

        # prune 0-counts
        while counts_reversed[0]['count'] == 0:
            counts_reversed.pop(0)

        if len(counts_reversed) < dans_cfg['minimum_time_periods']:
            continue

        # Take the last quarters to assess if the file type was in decline
        maybe_declining_period = quarterly_counts[-dans_cfg['decline_periods']:]
        quarterly_changes = np.diff([p['count'] for p in maybe_declining_period])

        # Ignore the file types with stable or increasing number quarterly_changes
        if quarterly_changes.mean() >= 0:
            continue

        # We do the exercise above because the mime types included in the "mime_plots" list was decided based on the
        # filters above
        if filetype not in dans_cfg['mime_plots']:
            continue

        # Keep the rest
        keep_filetypes.append(filetype)

    logging.info(f'Keeping {len(keep_filetypes)} filetypes for analysis: {keep_filetypes}')
    kept_counts = {filetype: counts for filetype, counts in quarterly_stats.items() if filetype in keep_filetypes}
    plot_counts(kept_counts, dans_cfg)

    return 0


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Data Archiving and Networked Services file metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
