"""
Module for scraping file metadata from the DANS Archaeology Datastation.
The scrape harvests only metadata from the files as originally deposited, not the files being offered as converted to
preferred formats. This way, we can analyze the original file formats in use at the time of deposition.
Good example: https://archaeology.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-zbe-b8h5

In order to extract this specific metadata, the `main` script filters data on the following:
1. It iterates over all pages in the datasets index of the Archaeology Datastation (~120k results in ~12k pages)
2. It extracts the digital object identifier (DOI) from the links to the datasets
3. It rejects all datasets having a description "Files not yet migrated to Data Station"
4. It gets the versions metadata for the dataset
5. It appends the versions metadata to a scrape log as ndjson-formatted file

TODO:
  - One version labeled "EASY Migration":
    see https://archaeology.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-28e-mmdt
  - Two or more versions labeled "EASY Migration":
    see https://archaeology.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-x8z-d4he,
"""
import datetime
import json
import logging
from argparse import ArgumentParser
from http.client import HTTPSConnection
from math import ceil
from typing import List, Dict, Optional

from bs4 import BeautifulSoup
from tqdm import tqdm

from analysis.config import Config, load_config
from analysis.loaders_dumpers import get


def main(config: Config) -> int:
    """
    Iterates over all pages in the datasets index of the Archaeology Datastation (~120k results in ~12k pages)

    :param config: a analysis.config.Config instance

    :return: 0
    """
    start = datetime.datetime.now()

    dans_cfg = config['data']['dans']
    url = dans_cfg['root_url']

    connection = HTTPSConnection(url.split('/')[-1])
    res_text = get(url, connection)
    soup = BeautifulSoup(res_text, features="html.parser")
    results_count = soup.find(class_='results-count').text.split(' ')

    total = int(results_count[4].replace(',', ''))
    page_size = int(results_count[2])
    num_pages = ceil(total / page_size)

    num_skipped_datasets = 0

    for page_num in tqdm(range(dans_cfg['start_page'], num_pages)):
        dois = dois_from_results(page_num, connection, dans_cfg)

        # Extract the file metadata for each dataset (by DOI)
        for doi in dois:
            version_metadata = scrape_version_metadata(doi, connection, dans_cfg)
            if version_metadata is None:
                num_skipped_datasets += 1
                continue

            # Append the version metadata for the dataset to the newline-delimited json scrape log
            with open(dans_cfg['scrape_log_path'], 'at') as f:
                f.write(json.dumps(version_metadata) + '\n')

            filenames, deposit_date = version_metadata
            filetype_counts: Dict[str, int] = {}

            # Update the monthly file extension counts by going over all the v1 files in the dataset
            for file in filenames:
                # Skip filenames without file extension
                if '.' not in file:
                    continue

                extension = file.split('.')[-1]
                filetype_counts.setdefault(extension, 0)
                filetype_counts[extension] += 1

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


def dois_from_results(page_num: int, conn: HTTPSConnection, dans_cfg: dict) -> List[str]:
    """
    Processes a specific results page indicated by `page_num` from the main Archaeology Datastation datasets index

    :param page_num:    The page number of the complete result set, as a whole positive number
    :param dans_cfg:    The DANS configuration parsed extracted from a Config instance

    :return: A list of DOIs as strings
    """
    root_url = dans_cfg['root_url']
    page_subpath = dans_cfg['page_subpath'].format(page=page_num)

    url = root_url + page_subpath
    res_text = get(url, conn)
    dois = extract_dois(res_text)

    return dois


def extract_dois(res_text: str) -> List[str]:
    """
    Extracts the digital object identifier (DOI) from the links to the datasets on a datasets results page.

    :param res_text: The HTML text of a Archaeology Datastation datasets results page

    :return: A list of extracted DOIs as strings
    """
    soup = BeautifulSoup(res_text, features="html.parser")

    dois: List[str] = []

    for dataset in soup.find_all(class_='card-title-icon-block'):
        hyperlink = dataset.a['href']
        doi = hyperlink.split('=')[1]
        dois.append(doi)

    return dois


def scrape_version_metadata(doi: str, conn: HTTPSConnection, dans_cfg: dict) -> Optional[dict]:
    """
    Extracts a list of original filenames and a deposit date for a dataset designated by `doi`

    It returns None for a dataset having
        - a description "Files not yet migrated to Data Station"
        - no two versions
        - no version 1

    :param doi:         Digital object identifier for the dataset
    :param dans_cfg:    DANS Archaeology datastation extracted from a Config instance

    :return:            A tuple of a list of filenames and a deposit date, or None if requirements ar not met.
    """
    root_url = dans_cfg['root_url']
    overview_subpath = dans_cfg['dataset_overview_api_subpath']
    url = root_url + overview_subpath.format(doi=doi)
    res = json.loads(get(url, conn))

    # Return empty list for datasets not yet migrated
    for citation_field in res['data']['latestVersion']['metadataBlocks']['citation']['fields']:
        if citation_field['typeName'] == 'dsDescription':
            for value in citation_field['value']:
                if 'not yet migrated' in value['dsDescriptionValue']['value']:
                    logging.debug(f"Skipping {doi}: not yet migrated")
                    return None

    # Inspect the available dataset versions
    versions_subpath = dans_cfg['dataset_versions_api_subpath']
    url = root_url + versions_subpath.format(doi=doi)
    versions = json.loads(get(url, conn))

    return versions


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
