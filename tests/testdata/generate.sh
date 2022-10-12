#!/usr/bin/env bash
# Get a random cdx gzip file from Common Crawl
wget 'https://data.commoncrawl.org/cc-index/collections/CC-MAIN-2017-39/indexes/cdx-00000.gz'
# Unzip it
gunzip cdx-00000.gz
# Extract the first 100 entries and re-gzip to a smaller sample gzip file
head -n 100 cdx-00000 | gzip -c > ~/Documents/Git/NDE-monitoring-file-formats/tests/testdata/sample.gz
# Ditch the large gzip file
rm cdx-00000.gz
