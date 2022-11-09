"""
Module for scraping file metadata from the DANS Archaeology Datastation.
The scrape harvests only metadata from the files as originally deposited, not the files being offered as converted to
preferred formats. This way, we can analyze the original file formats in use at the time of deposition.
Good example: https://archaeology.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-zbe-b8h5

In order to extract this specific metadata, the `main` script filters data on the following:
1. It iterates over all pages in the datasets index of the Archaeology Datastation (~120k results in ~12k pages)
2. It extracts the digital object identifier (DOI) from the links to the datasets
3. It rejects all datasets having a description "Files not yet migrated to Data Station"
4. It accepts all datasets with - Version: either
  - One version labeled "EASY Migration":
    see https://archaeology.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-28e-mmdt
  - Two or more versions labeled "EASY Migration":
    see https://archaeology.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-x8z-d4he,
  - Two or more versions, only the version with summary "This is the first published version.":
    see: https://archaeology.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-zbe-b8h5
6. For each dataset, for each file it extracts the deposit date
7. It logs the result cursor and metadata in order to resume on error
8. It aggregates the file metadata into a counter per file type, per month
"""
import json
from argparse import ArgumentParser
from math import ceil
from typing import List, Tuple

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
    dans_cfg = config['data']['dans']
    url = dans_cfg['root_url']

    res_text = get(url)
    soup = BeautifulSoup(res_text)
    results_count = soup.find(class_='results-count').text.split(' ')

    total = int(results_count[4].replace(',', ''))
    page_size = int(results_count[2])
    num_pages = ceil(total / page_size)

    for page_num in tqdm(range(dans_cfg['start_page'], num_pages)):
        dois = process_datasets_page(page_num, dans_cfg)

        for doi in dois:
            extract_file_metadata(doi, dans_cfg)
            continue

        break

    return 0


def process_datasets_page(page_num: int, dans_cfg: dict) -> List[str]:
    """
    Processes a specific results page indicated by `page_num` from the main Archaeology Datastation datasets index

    :param page_num:    The page number of the complete result set, as a whole positive number
    :param dans_cfg:    The DANS configuration parsed extracted from a Config instance

    :return: A list of DOIs as strings
    """
    root_url = dans_cfg['root_url']
    page_subpath = dans_cfg['page_subpath'].format(page=page_num)

    url = root_url + page_subpath
    res_text = get(url)
    dois = extract_dois(res_text)

    return dois


def extract_dois(res_text: str) -> List[str]:
    """
    Extracts the digital object identifier (DOI) from the links to the datasets on a datasets results page.

    :param res_text: The HTML text of a Archaeology Datastation datasets results page

    :return: A list of extracted DOIs as strings
    """
    soup = BeautifulSoup(res_text)

    dois: List[str] = []

    for dataset in soup.find_all(class_='card-title-icon-block'):
        hyperlink = dataset.a['href']
        doi = hyperlink.split('=')[1]
        dois.append(doi)

    return dois


def extract_file_metadata(doi: str, dans_cfg: dict) -> List[Tuple[str, str]]:
    """
    Extracts original file names and deposit dates for a dataset designated by `doi`

    It returns an empty list for a dataset having a description "Files not yet migrated to Data Station"
    It accepts a dataset with a valid version: either
      - One version labeled "EASY Migration" and summary "This is the first published version."
      - Two or more versions, only the version with summary "This is the first published version.":
        see: https://archaeology.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-zbe-b8h5
      - Two or more versions labeled "EASY Migration": TODO

    :param doi:         Digital object identifier for the dataset
    :param dans_cfg:    DANS Archaeology datastation extracted from a Config instance

    :return:            A list of tuples, each containing a filename and a deposit date. May return an empty list.
    """
    root_url = dans_cfg['root_url']
    overview_subpath = dans_cfg['dataset_overview_api_subpath']
    url = root_url + overview_subpath.format(doi=doi)
    res = json.loads(get(url))

    # Return empty list for datasets not yet migrated
    for citation_field in res['data']['latestVersion']['metadataBlocks']['citation']['fields']:
        if citation_field['typeName'] == 'dsDescription':
            for value in citation_field['value']:
                if 'Dataset not yet migrated' in value['dsDescriptionValue']['value']:
                    return []

    versions_subpath = dans_cfg['dataset_versions_api_subpath']

    url = root_url + versions_subpath.format(doi=doi)
    res = json.loads(get(url))

    return []


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
