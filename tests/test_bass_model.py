import numpy as np
from numpy.testing import assert_array_equal

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

    # Test equality of the `sales at time` function with model.predict
    prediction1 = model.sales_at_time(model.bass_parameters, t)
    prediction2 = model.predict(t)
    assert_array_equal(prediction1, prediction2)
