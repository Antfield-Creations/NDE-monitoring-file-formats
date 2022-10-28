"""
Module to create aggregated statistics - per file format, per period - for raw record data acquired from
Nederlands Instituut voor Beeld en Geluid, courtesy of Mari Wigham.
"""
import datetime
import logging
from argparse import ArgumentParser

from analysis.config import load_config, Config


def main(config: Config) -> int:
    start = datetime.datetime.now()

    line_counter = 0
    with open(config['data']['nibg']['raw_csv_path'], 'rt') as f:
        for record in f:
            line_counter += 1
            record = f.readline()

            if line_counter % 1000000 == 0:
                logging.info(f'Line {line_counter}')

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Common Crawl MIME type usage-over-time analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
