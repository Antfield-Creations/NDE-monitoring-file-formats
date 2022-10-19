"""
Bass diffusion model, by Frank Bass, 1969. Allows you to project sales at specified times based on a sigmoidal-shaped
cumulative function, parameterized by a market potential (m), an innovators factor (p), and an imitators factor (q).

This module was adapted from
https://github.com/NForouzandehmehr/Bass-Diffusion-model-for-short-life-cycle-products-sales-prediction/blob/master/bass.py
"""
from dataclasses import dataclass
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares, OptimizeResult


@dataclass
class BassParameters:
    m: Union[int, float] = 50000
    p: float = 0.03
    q: float = 0.38


class BassDiffusionModel:
    def __init__(self, m: int = None, p: float = None, q: float = None):
        """
        Initializes the Bass diffusion model parameters m, p and q with default (overridden if needed) values
        :param m:       Market potential coefficient
        :param p:       Innovators coefficient
        :param q:       Imitators coefficient
        """
        if m is not None and p is not None and q is not None:
            self.bass_parameters = BassParameters(float(m), float(p), float(q))
        else:
            self.bass_parameters = BassParameters()

    @staticmethod
    def sales_at_time(
            bass_parameters: BassParameters, time: Union[int, float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """
        This function represents the Bass sales prediction function, calling it with a specified `time` will
        provide the projected sales at `time`.

        :param bass_parameters: The parameters object of a Bass model, having properties m, p, and q
        :param time:            The time for which to make the Bass sales projection, supplied as a positive number or
                                numpy array of positive numbers

        :return: The projected sales at time `time` as a single float value or a numpy array of floats
        """
        bass = bass_parameters.m * (
                ((bass_parameters.p + bass_parameters.q) ** 2 / bass_parameters.p) *
                BassDiffusionModel.cofactor(bass_parameters, time)
        ) / (1 + (bass_parameters.q / bass_parameters.p) * BassDiffusionModel.cofactor(bass_parameters, time)) ** 2

        return bass

    @staticmethod
    def cofactor(bass_parameters: BassParameters, time: Union[int, float, np.ndarray]) -> np.ndarray:
        return np.exp(-(bass_parameters.p + bass_parameters.q) * time)

    @staticmethod
    def residual(bass_parameter_estimations: np.ndarray, time: int, expected_sales: int) -> float:
        """
        Residual error function that calculates the difference between the Bass model output given coefficients
        m, p, q at time `time` (see below) on the one hand and the actual sales figure on the other hand.

        :param bass_parameter_estimations: Tuple of values m, p and q
        :param time:            A specific time
        :param expected_sales:  The actual (expected) sales value

        :return: The difference between the calculated Bass function output and the actual provided sales figure
        """
        parameters = BassParameters(*bass_parameter_estimations)
        projected_sales = BassDiffusionModel.sales_at_time(parameters, time)

        return projected_sales - expected_sales

    def fit(self, times: np.ndarray, sales: np.ndarray) -> None:
        """
        Performs non-linear least square fitting of Bass parameters based on provided `sales` at `times`.
        Updates the Bass parameters based on the optimal values found.

        :param times:   numpy 1-dimensional array of times
        :param sales:   numpy 1-dimensional array of sales matching with `times`
        :return:
        """
        default_params = BassParameters()
        # A start estimate of 100 times the max sales appears to be a reasonable value
        initial_estimate_m = np.max(sales) * 100

        result: OptimizeResult = least_squares(
            # Distance function
            fun=BassDiffusionModel.residual,
            # Starting estimate
            x0=np.array([initial_estimate_m, default_params.p, default_params.q]),
            # Extra arguments to the function that are not part of the estimation
            args=(times, sales),
            max_nfev=1000,
        )

        if result['status'] < 1:
            raise RuntimeError(f'Optimal parameters could not be found: {result["message"]}')

        optimal = result['x']

        # update estimated coefficients
        self.bass_parameters.m = optimal[0]
        self.bass_parameters.p = optimal[1]
        self.bass_parameters.q = optimal[2]

    def plot_sales_pdf(self, times: np.ndarray, interpolated_times: np.ndarray, expected_sales: np.ndarray) -> None:
        projected_sales = self.sales_at_time(self.bass_parameters, interpolated_times)

        plt.plot(interpolated_times, projected_sales, times, expected_sales)
        plt.title('Sales pdf')
        plt.legend(['Fit', 'True'])
        plt.show()

    def plot_sales_cdf(self) -> None:
        # time interpolation
        t = np.linspace(1.0, 10.0, num=10)

        # expected_sales vector
        sales = np.array([840, 1470, 2110, 4000, 7590, 10950, 10530, 9470, 7790, 5890])

        # time intervals
        tp = np.linspace(1.0, 100.0, num=100) / 10

        # Cumulative expected_sales (cdf)
        cumulative_sales = np.cumsum(sales)
        sales_cdf = self.bass_parameters.m * (
            1 - self.cofactor(self.bass_parameters, tp)
        ) / (1 + (self.bass_parameters.q / self.bass_parameters.p) * self.cofactor(self.bass_parameters, tp))

        plt.plot(tp, sales_cdf, t, cumulative_sales)
        plt.title('Sales cdf')
        plt.legend(['Fit', 'True'])
        plt.show()
