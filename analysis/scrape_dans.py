import urllib.request
from argparse import ArgumentParser

from bs4 import BeautifulSoup

from analysis.config import Config, load_config


def main(config: Config) -> int:
    dans_cfg = config['data']['dans']

    with urllib.request.urlopen(dans_cfg['start_index']) as f:
        if f.status != 200:
            raise RuntimeError(f'Invalid response {f.status}')

        res_text = f.read().decode('utf-8')
        soup = BeautifulSoup(res_text)

    return 0


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
