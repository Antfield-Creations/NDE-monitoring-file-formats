import numpy as np

from models.bass_diffusion import BassDiffusionModel


def test_model_predictions() -> None:
    model = BassDiffusionModel()

    sales = np.array([840, 1470, 2110, 4000, 7590, 10950, 10530, 9470, 7790, 5890])

    # time interpolation
    t = np.linspace(1.0, float(len(sales)), num=10)

    # time intervals
    tp = np.linspace(0.1, float(len(sales)), num=100)

    model.fit(times=t, sales=sales)

    assert 70000 > model.bass_parameters.m > 60000
    model.plot_sales_pdf(t, tp, sales)
