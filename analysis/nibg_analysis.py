import datetime
import json
import logging
import os
from argparse import ArgumentParser

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

from analysis.config import load_config, Config
from analysis.shared_parsers import extract_year_ticks, to_pruned_sorted_quarterly, SortedFileCount
from models.bass_diffusion import BassDiffusionModel


def main(config: Config) -> int:
    start = datetime.datetime.now()
    nibg_cfg = config['data']['nibg']

    aggregate_stats_path = os.path.join(nibg_cfg['json_output_dir'], 'nibg_aggregate_stats.json')
    with open(aggregate_stats_path, 'rt') as f:
        aggregate_stats = json.loads(f.read())

    quarterly_counts = to_pruned_sorted_quarterly(aggregate_stats)
    plot_counts(quarterly_counts, nibg_cfg)

    end = datetime.datetime.now()
    logging.info(f'Script took {end - start}')

    return 0


def plot_counts(counts: SortedFileCount, nibg_cfg: dict) -> None:
    output_dir = nibg_cfg['img_output_dir']
    num_tests = nibg_cfg['num_test_measurements']

    for file_type, quarter_counts in counts.items():
        quarters = [entry['period'] for entry in quarter_counts]

        # Set up training and test data
        all_times = list(range(len(quarters)))
        train_times = all_times[:-num_tests]
        test_times = all_times[-num_tests:]

        all_counts = [entry['count'] for entry in quarter_counts]
        train_counts = all_counts[:-num_tests]
        # test_counts = all_counts[-num_tests:]

        # Fit the Bass model and produce data
        bass_model = BassDiffusionModel()
        train_inputs = np.array(train_times)
        test_inputs = np.array(test_times)
        bass_model.fit(train_inputs, np.array(train_counts))
        fitted_values = bass_model.sales_at_time(bass_model.bass_parameters, train_inputs)
        projected_values = bass_model.sales_at_time(bass_model.bass_parameters, test_inputs)

        plot_data = [
            all_times, all_counts,
            train_times, fitted_values,
            test_times, projected_values
        ]
        legend_data = [
            'Aantal bestanden',
            'Bass "fit"',
            'Bass "test"'
        ]

        if file_type in nibg_cfg['linear_plots']:
            # Fit linear model for selected file formats
            linear_model = LinearRegression()
            max_idx = train_counts.index(max(train_counts))
            linear_train_times = np.expand_dims(all_times[max_idx:-num_tests], 1)
            linear_train_counts = all_counts[max_idx:-num_tests]
            linear_test_times = np.expand_dims(all_times[-num_tests:], 1)

            linear_model.fit(linear_train_times, linear_train_counts)
            linear_fitted_values = linear_model.predict(linear_train_times)
            linear_projected_values = linear_model.predict(linear_test_times)

            plot_data.extend([linear_train_times, linear_fitted_values])
            plot_data.extend([linear_test_times, linear_projected_values])
            legend_data.append('Lineair "fit"')
            legend_data.append('Lineair "test"')

        plt.plot(*plot_data)
        x_axis_labels = extract_year_ticks(quarters, separator='Q', index=0)
        plt.title(f"NIBG tellingen voor bestandstype {file_type}")
        plt.xticks(all_times, x_axis_labels, rotation=45)
        plt.legend(legend_data)
        plt.savefig(os.path.join(output_dir, f'{file_type}.png'))
        plt.show()


if __name__ == '__main__':
    parser = ArgumentParser('Performs the Nederlands Instituut voor Beeld en Geluid metadata analysis')
    parser.add_argument('-c', '--config', default='config.yaml')

    args = parser.parse_args()
    config = load_config(args.config)
    raise SystemExit(main(config))
