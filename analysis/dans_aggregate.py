"""
Analysis module for the DANS file metadata. Run python -m analysis.dans_scrape first to collect the file metadata into
a scrape ndjson log, then run this script to analyze it using python -m analysis.dans_analyze
"""

import datetime
import json
import logging
from argparse import ArgumentParser
from typing import Dict, Optional, Tuple, List

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
        for count, _ in enumerate(f):
            pass

    logging.info(f'Log has {count + 1} entries')

    with open(dans_cfg['scrape_log_path'], 'rt') as f:
        for json_record in tqdm(f, total=count + 1):
            record = json.loads(json_record)
            result = extract_file_metadata(record, dans_cfg)

            if result is None:
                continue

            # Unpack the tuple now we know it's not empty
            file_names, timestamp = result
            # Get the file extension from the filename if it contains a file extension identifiable by a dot
            file_types = [f.split('.')[-1] for f in file_names if '.' in f]

            for file_type in file_types:
                file_stats.setdefault(file_type, {})
                year_month = timestamp[:6]
                file_stats[file_type].setdefault(year_month, 0)
                file_stats[file_type][year_month] += 1

    with open(dans_cfg['filetype_monthly_aggregate_path'], 'wt') as f:
        f.write(json.dumps(file_types))

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


def extract_file_metadata(ds_metadata: dict, dans_cfg: Dict[str, str]) -> Optional[Tuple[List[str], str]]:
    """
    Analyses a metadata record from the archaeology datastation REST API
    It accepts datasets with:
      - Two versions, one version migrated from DANS EASY and one with preferred file formats
        example: https://archaeology.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-zbe-b8h5
    It collects the file metadata of the first version.
    For each dataset, the correct date for the first version files
    It aggregates the file metadata into a counter per file type, per month

    :param ds_metadata: metadata dictionary for a dataset, gotten from the archaeology dataverse REST API
    :param dans_cfg:    The DANS scrape and analysis configuration, from the config.yaml `dans` section

    :return:    Either a tuple with a list of file types and a date for them,
                or None if the data does not match the criteria
    """
    # sanity check!
    if 'data' not in ds_metadata.keys():
        logging.error(f'Metadata has no "data": {ds_metadata}')
        return None

    versions = ds_metadata['data']

    # sanity check again
    if len(versions) == 0:
        logging.error(f'Metadata has no versions: {ds_metadata}')
        return None

    if 'datasetPersistentId' not in versions[0].keys():
        logging.error(f'Metadata version 1 has no persistent identifier: {ds_metadata}')
        return None

    doi = versions[0]['datasetPersistentId']

    # Return an empty result if there are not two versions of the dataset: one of the original deposited data files,
    # and one offering the data in preferred formats
    if len(versions) != 2:
        logging.debug(f'Skipping: no two versions for {doi}, but {len(versions)}')
        return None

    # Return an empty result if there is no single version 1 of the dataset
    first_version_candidates = [version for version in versions if version['versionNumber'] == 1]
    if len(first_version_candidates) != 1:
        version_numbers = [version['versionNumber'] for version in versions['data']]
        logging.error(f"Skipping {doi}, no version 1 in {version_numbers}")
        return None

    first_version = first_version_candidates[0]
    citation_fields = first_version['metadataBlocks']['citation']['fields']
    maybe_date_of_deposit = [field for field in citation_fields if field['typeName'] == 'dateOfDeposit']
    # Return an empty result if there is not a singular deposit date
    if len(maybe_date_of_deposit) != 1:
        logging.error(f"Skipping {doi}: no date of deposit found")
        return None

    deposit_date = maybe_date_of_deposit[0]['value']
    filenames = [file['label']for file in first_version['files']]

    # Filter out unwanted files
    filenames = [file for file in filenames if file not in dans_cfg['file_skip_list']]

    return filenames, deposit_date


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Data Archiving and Networked Services file metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
