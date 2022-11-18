import json
import os

from analysis.config import load_config
from analysis.nibg_analysis import to_pruned_sorted_quarterly


def test_quarterly_counts() -> None:
    config = load_config()
    nibg_cfg = config['data']['nibg']

    aggregate_stats_path = os.path.join(nibg_cfg['json_output_dir'], 'nibg_aggregate_stats.json')
    with open(aggregate_stats_path, 'rt') as f:
        aggregate_stats = json.loads(f.read())

    mxf_stats = aggregate_stats['mxf']
    # Drop the incomplete counts for the last quarter
    del mxf_stats['2022-10']
    monthly_summed = sum(mxf_stats.values())
    quarterly_stats = to_pruned_sorted_quarterly(aggregate_stats)
    mxf_stats = quarterly_stats['mxf']
    mxf_counts = [entry['count'] for entry in mxf_stats]
    quarterly_summed = sum(mxf_counts)

    assert monthly_summed == quarterly_summed, 'sum of monthly counts should match the sum of quarterly counts'
