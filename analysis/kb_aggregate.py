"""
Module to create aggregated statistics - per file format, per period - for raw record data acquired from
KB
"""
import datetime
import json
import logging
import os.path
from argparse import ArgumentParser
from typing import List

from tqdm import tqdm

from analysis.config import load_config, Config


def main(config: Config) -> int:
    start = datetime.datetime.now()

    kb_cfg = config['data']['kb']
    file_temp_stats: dict = {}
    skipped_records = 0

    with open(kb_cfg['raw_csv_path'], 'rt') as f:
        for line_no, record in enumerate(tqdm(f, total=kb_cfg['raw_csv_line_count'])):
            # Skip header with column names
            if line_no == 0:
                # header = record.split(',')
                continue

            parts = record.split('|')

            mimetype = str(parts[1])
            create_date = parts[0]

            file_temp_stats.setdefault(mimetype, {})

            year_month = '-'.join(create_date.split('-')[1:3])
            #year_month = create_date.split('-')[2:3][0]
            file_temp_stats[mimetype].setdefault(year_month, 0)
            file_temp_stats[mimetype][year_month] += 1

    # Prune stats for formats that have at least 10 entries
    formats = list(file_temp_stats.keys())
    dropped_formats: List[str] = []
    min_measurements = kb_cfg['minimum_time_periods']

    for mimetype in formats:
        num_measurements = len(file_temp_stats[mimetype].keys())
        if num_measurements < min_measurements:
            logging.warning(f"Excluded {mimetype}: only {num_measurements} available, minimum is {min_measurements}")
            del file_temp_stats[mimetype]
            dropped_formats.append(mimetype)

    output_path = os.path.join(kb_cfg['json_output_dir'], 'kb_aggregate_stats.json')
    with open(output_path, 'wt') as f:
        f.write(json.dumps(file_temp_stats, indent=2))

    logging.info(f'Wrote stats to {output_path}')
    logging.info('Counts:')
    for format in file_temp_stats.keys():
        total = sum([count for count in file_temp_stats[format].values()])
        logging.info(f'{format=} {total=}')

    logging.info(f'Skipped {skipped_records} records')
    logging.info(f'{dropped_formats=}')

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


if __name__ == '__main__':
    parser = ArgumentParser('Performs the KB file archive metadata aggregation')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
