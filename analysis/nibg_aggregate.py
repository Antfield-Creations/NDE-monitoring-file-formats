"""
Module to create aggregated statistics - per file format, per period - for raw record data acquired from
Nederlands Instituut voor Beeld en Geluid, courtesy of Mari Wigham.
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

    nibg_cfg = config['data']['nibg']
    file_temp_stats: dict = {}
    skipped_records = 0

    with open(nibg_cfg['raw_csv_path'], 'rt') as f:
        for line_no, record in enumerate(tqdm(f, total=nibg_cfg['raw_csv_line_count'])):
            # Skip header with column names
            if line_no == 0:
                # header = record.split(',')
                continue

            parts = record.split(',')

            filename = str(parts[2])
            filetype = str(parts[3])
            # Skip if there is no dot in the filename to separate the file name extension
            if '.' not in filename:
                if filetype == '':
                    skipped_records += 1
                    continue
                else:
                    filename = filetype

            create_date = parts[5]
            if create_date == '' or create_date == 'true':
                skipped_records += 1
                continue

            extension = filename.split('.')[-1].lower()
            file_temp_stats.setdefault(extension, {})

            year_month = '-'.join(create_date.split('-')[0:2])
            file_temp_stats[extension].setdefault(year_month, 0)
            file_temp_stats[extension][year_month] += 1

    # Prune stats for formats that have at least 10 entries
    formats = list(file_temp_stats.keys())
    dropped_formats: List[str] = []
    min_measurements = nibg_cfg['minimum_time_periods']

    for extension in formats:
        num_measurements = len(file_temp_stats[extension].keys())
        if num_measurements < min_measurements:
            logging.warning(f"Excluded {extension}: only {num_measurements} available, minimum is {min_measurements}")
            del file_temp_stats[extension]
            dropped_formats.append(extension)

    output_path = os.path.join(nibg_cfg['json_output_dir'], 'nibg_aggregate_stats.json')
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
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid file archive metadata aggregation')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
