import datetime
import gzip
import json
import logging
import os
from argparse import ArgumentParser
from collections import Counter
from urllib import request

from analysis.config import load_config, Config


def main(config: Config):
    crawl_cfg = config['data']['common_crawl']
    with open(crawl_cfg['index_file'], 'rt') as f:
        cc_roots = json.loads(f.read())

    for crawl_month in cc_roots:
        if crawl_month['id'] < crawl_cfg['start_from']:
            continue

        url = crawl_cfg['url_index_download_template'].format(crawl_entry=crawl_month['id'])
        logging.info(f'Retrieving {url}')
        gzip_path = os.path.join(crawl_cfg['download_dir'], 'cc-index.paths.gz')
        request.urlretrieve(url, gzip_path)

        with gzip.open(gzip_path, 'rb') as f:
            cdx_urls = f.read().decode()

        for index in cdx_urls.split('\n'):
            filename = index.split('/')[-1]
            cdx_gz = os.path.join(crawl_cfg['download_dir'], filename)
            logging.info(f'Retrieving {index} to {cdx_gz}')
            request.urlretrieve(index, cdx_gz)

            logging.info(f'Analysing {index}')
            analysis = analyse(cdx_gz)
            print(analysis)


def analyse(gzip_path) -> Counter:
    counter = Counter()

    with gzip.open(gzip_path, 'rt') as f:
        while True:
            url = f.readline()
            if url is None or url == '':
                break

            json_start = url.find('{"url"')
            entry_json = url[json_start:]
            entry = json.loads(entry_json)

            # Handle only response OK entries
            if entry['status'] != '200':
                continue

            counter.update([entry['mime-detected']])

    return counter


if __name__ == '__main__':
    start = datetime.datetime.now()
    parser = ArgumentParser('Performs the Common Crawl MIME type usage over time analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    main(config)
    logging.info(f'Took {datetime.datetime.now() - start}')
