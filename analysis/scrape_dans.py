import urllib.request
from argparse import ArgumentParser
from math import ceil

from bs4 import BeautifulSoup
from tqdm import tqdm

from analysis.config import Config, load_config


def main(config: Config) -> int:
    dans_cfg = config['data']['dans']
    root_url = dans_cfg['root_url']

    with urllib.request.urlopen(root_url) as f:
        if f.status != 200:
            raise RuntimeError(f'Invalid response {f.status}')

        res_text = f.read().decode('utf-8')
        soup = BeautifulSoup(res_text)
        results_count = soup.find(class_='results-count').text.split(' ')

    total = int(results_count[4].replace(',', ''))
    page_size = int(results_count[2])
    num_pages = ceil(total / page_size)

    for page_num in tqdm(range(num_pages)):
        subpath = dans_cfg['page_subpath'].format(page=page_num)
        with urllib.request.urlopen(dans_cfg['start_index'] + subpath) as f:
            if f.status != 200:
                raise RuntimeError(f'Invalid response {f.status}')

            res_text = f.read().decode('utf-8')

        soup = BeautifulSoup(res_text)
        for dataset in soup.find_all(class_='card-title-icon-block'):
            hyperlink = dataset.a['href']
            pass

        break

    return 0


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
