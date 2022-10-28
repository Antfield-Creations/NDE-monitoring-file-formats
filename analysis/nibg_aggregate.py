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
    file_temp_stats = {}
    skipped_records = 0

    with open(nibg_cfg['raw_csv_path'], 'rt') as f:
        for line_no, record in enumerate(tqdm(f, total=nibg_cfg['raw_csv_line_count'])):
            # Skip header with column names
            if line_no == 0:
                header = record.split(',')
                continue

            parts = record.split(',')

            format = parts[3]
            file_temp_stats.setdefault(format, {})

            create_date = parts[5]
            if create_date == '' or create_date == 'true':
                skipped_records += 1
                continue

            year_month = '-'.join(create_date.split('-')[0:2])
            file_temp_stats[format].setdefault(year_month, 0)
            file_temp_stats[format][year_month] += 1

    # Prune stats for formats that have at least 10 entries
    formats = list(file_temp_stats.keys())
    dropped_formats: List[str] = []

    for format in formats:
        if len(file_temp_stats[format].keys()) < nibg_cfg['minimum_time_periods']:
            del file_temp_stats[format]
            dropped_formats.append(format)

    output_path = os.path.join(nibg_cfg['json_output_dir'], 'nibg_aggregate_stats.json')
    with open(output_path, 'wt') as f:
        f.write(json.dumps(file_temp_stats, indent=2))
    logging.info(f'Wrote stats to {output_path}')
    logging.info(f'Skipped {skipped_records} records')
    logging.info(f'{dropped_formats=}')

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Common Crawl MIME type usage-over-time analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
