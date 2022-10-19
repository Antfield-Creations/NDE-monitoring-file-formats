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
    def __init__(self, m: int = 60630, p: float = 0.03, q: float = 0.38):
        """
        Initializes the Bass diffusion model parameters m, p and q with default (overridden if needed) values
        :param m:       Market potential coefficient
        :param p:       Innovators coefficient
        :param q:       Imitators coefficient
        """
        self.m, self.p, self.q = m, p, q

    def sales_at_time(self, time: Union[int, float]) -> float:
        """
        This function represents the Bass sales prediction function, calling it with a specified parameter time will
        provide the projected sales at time `time`.

        :param time: The time for which to make the Bass sales projection

        :return: The projected sales at time `time` as a single float value
        """
        bass = self.m * (
                ((self.p + self.q) ** 2 / self.p) * self.cofactor(time)
        ) / (1 + (self.q / self.p) * self.cofactor(time)) ** 2

        return bass

    def sales_probability_distribution_function(self, times: np.ndarray) -> np.ndarray:
        """
        This is basically the vectorized version of self.sales_at_time. It allows you to project the sales for a
        numpy array of times, returning an array of projected sales

        :param times: A numpy 1-dimensional array of times

        :return: A numpy 1-dimensional array of projected sales
        """
        sales_pdf = self.m * (
                ((self.p + self.q) ** 2 / self.p) * self.cofactor(times)
        ) / (1 + (self.q / self.p) * self.cofactor(times)) ** 2

        return sales_pdf

    def cofactor(self, tp):
        return np.exp(-(self.p + self.q) * tp)

    def residual(self, time: int, expected_sales: int) -> float:
        """
        Residual error function that calculates the difference between the Bass model output given coefficients
        m, p, q at time `time` (see below) on the one hand and the actual sales figure on the other hand.

        :param time:            A specific time
        :param expected_sales:  The actual (expected) sales value

        :return: The difference between the calculated Bass function output and the actual provided sales figure
        """
        bass = self.sales_at_time(time)
        return bass - expected_sales

    def fit(self, times: np.ndarray, sales: np.ndarray) -> None:
        """
        Performs non-linear least square fitting of Bass parameters based on provided `sales` at `times`.
        Updates the Bass parameters based on the optimal values found.

        :param times:   numpy 1-dimensional array of times
        :param sales:   numpy 1-dimensional array of sales matching with `times`
        :return:
        """
        optimal = leastsq(
            func=self.residual,                         # Distance function
            x0=np.array([self.m, self.p, self.q]),      # The starting estimate
            args=(times, sales))            # Extra arguments to the function that are not part of the estimation

        # update estimated coefficients
        self.m = optimal[0]
        self.p = optimal[1]
        self.q = optimal[2]

    def plot_sales_pdf(self, tp: np.ndarray) -> None:
        # expected_sales plot (pdf)
        # time interpolation
        t = np.linspace(1.0, 10.0, num=10)

        # time intervals
        tp = np.linspace(1.0, 100.0, num=100) / 10

        sales_pdf = self.sales_probability_distribution_function(tp)

        # expected_sales vector
        sales = np.array([840, 1470, 2110, 4000, 7590, 10950, 10530, 9470, 7790, 5890])

        plt.plot(tp, sales_pdf, t, sales)
        plt.title('Sales pdf')
        plt.legend(['Fit', 'True'])
        plt.show()

    def plot_sales_cdf(self):
        # time interpolation
        t = np.linspace(1.0, 10.0, num=10)

        # expected_sales vector
        sales = np.array([840, 1470, 2110, 4000, 7590, 10950, 10530, 9470, 7790, 5890])

        # time intervals
        tp = np.linspace(1.0, 100.0, num=100) / 10

        # Cumulative expected_sales (cdf)
        cumulative_sales = np.cumsum(sales)
        sales_cdf = self.m * (1 - self.cofactor(tp)) / (1 + (self.q / self.p) * self.cofactor(tp))
        plt.plot(tp, sales_cdf, t, cumulative_sales)
        plt.title('Sales cdf')
        plt.legend(['Fit', 'True'])
        plt.show()
