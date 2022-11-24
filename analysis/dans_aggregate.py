"""
Analysis module for the DANS file metadata. Run python -m analysis.dans_scrape first to collect the file metadata into
a scrape ndjson log, then run this script to analyze it using python -m analysis.dans_analyze
"""

import datetime
import json
import logging
from argparse import ArgumentParser
from typing import Dict

from jsonpath_ng.ext import parse
from tqdm import tqdm

from analysis.config import load_config, Config

# Unordered key/val
FileTimeStats = Dict[str, Dict[str, int]]


def main(config: Config) -> int:
    """
    Iterates over all pages in the datasets index of the Archaeology Datastation (~120k results in ~12k pages)

    :param config: a analysis.config.Config instance

    :return: 0
    """
    start = datetime.datetime.now()
    dans_cfg = config['data']['dans']

    file_stats: FileTimeStats = {}

    # number of lines in the file
    with open(dans_cfg['scrape_log_path'], 'rt') as f:
        for record_count, _ in enumerate(f):
            pass

    logging.info(f'Log has {record_count + 1} entries')
    unusable_datasets: Dict[str, int] = {}

    with open(dans_cfg['scrape_log_path'], 'rt') as f:
        for json_record in tqdm(f, total=record_count + 1):
            record = json.loads(json_record)

            reason = explain_valid_dataset(record, dans_cfg)
            if reason != "Valid":
                unusable_datasets.setdefault(reason, 0)
                unusable_datasets[reason] += 1
                continue

            content_type_counts = extract_content_type_counts(record, dans_cfg)
            year_month = extract_year_month(record, dans_cfg)

            for content_type, count in content_type_counts.items():
                file_stats.setdefault(content_type, {})
                file_stats[content_type].setdefault(year_month, 0)
                file_stats[content_type][year_month] += count

    with open(dans_cfg['filetype_monthly_aggregate_path'], 'wt') as f:
        logging.info(f"Wrote aggregation to {dans_cfg['filetype_monthly_aggregate_path']}")
        f.write(json.dumps(file_stats, indent=2))

    logging.info(f'Unusable dataset reasons out of {record_count + 1}: {json.dumps(unusable_datasets, indent=2)}')

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


def explain_valid_dataset(ds_metadata: dict, dans_cfg: Dict[str, str]) -> str:
    """
    Analyses a metadata record from the archaeology datastation REST API to validate it for usage in this analysis

    :param ds_metadata: Dictionary with keys and values from the Dataverse version API
    :param dans_cfg: Simple key-value settings, found under config.yaml data -> dans

    :return: True if the dataset is valid, False if not
    """
    # sanity check
    if 'data' not in ds_metadata.keys():
        return 'Metadata has no "data" key'

    versions = ds_metadata['data']

    # sanity check again
    if len(versions) == 0:
        return 'Metadata has no versions'

    if 'datasetPersistentId' not in versions[0].keys():
        return 'Metadata version 1 has no persistent identifier'

    # Return invalid if there is no single version 1 of the dataset
    first_version_candidates = [version for version in versions
                                if version['versionNumber'] == 1 and version['versionMinorNumber'] == 0]
    if len(first_version_candidates) != 1:
        return 'No single version 1.0 for dataset'

    date_jsonpath = parse(dans_cfg['date_json_path'])
    matches = date_jsonpath.find(ds_metadata)

    # Return invalid if there is not a singular date
    if len(matches) != 1:
        return "No date found"

    return 'Valid'


def extract_content_type_counts(ds_metadata: dict, dans_cfg: Dict[str, str]) -> Dict[str, int]:
    """
    Collects the filenames of the first version of the dataset.

    :param ds_metadata: Metadata dictionary for a dataset, gotten from the archaeology dataverse REST API
    :param dans_cfg:    The DANS scrape and analysis configuration, from the config.yaml `dans` section

    :return:    Either a tuple with a list of file types and a date for them,
                or None if the data does not match the criteria
    """
    # Since the dataset is already validated, we can safely access the first 'data' entry with version 1
    content_types: Dict[str, int] = {}
    first_version = [version for version in ds_metadata['data']
                     if version['versionNumber'] == 1 and version['versionMinorNumber'] == 0][0]

    for file in first_version['files']:
        # Filter out unwanted files
        if file['label'] in dans_cfg['file_skip_list']:
            continue

        content_type = file['dataFile']['contentType']
        content_types.setdefault(content_type, 0)
        content_types[content_type] += 1

    return content_types


def extract_year_month(ds_metadata: dict, dans_cfg: Dict[str, str]) -> str:
    """
    Collects the correct date for the first version files
    It aggregates the file metadata into a counter per file type, per month

    :param ds_metadata: Metadata dictionary for a dataset, gotten from the archaeology dataverse REST API
    :param dans_cfg:    The DANS scrape and analysis configuration, from the config.yaml `dans` section

    :return: The extracted year and month in a single string formatted as "YYYY-mm"
    """
    date_jsonpath = parse(dans_cfg['date_json_path'])
    matches = date_jsonpath.find(ds_metadata)
    # Return an empty result if there is not a singular date
    if len(matches) != 1:
        raise ValueError(f"No date found for {ds_metadata=}: ")

    queried_date = matches[0].value

    return queried_date[:7]


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Data Archiving and Networked Services file metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
