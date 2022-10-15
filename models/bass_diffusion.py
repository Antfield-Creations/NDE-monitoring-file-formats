"""
This module was adapted from
https://github.com/NForouzandehmehr/Bass-Diffusion-model-for-short-life-cycle-products-sales-prediction/blob/master/bass.py
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import leastsq


def residual(m, p, q, t, sales):
    """
    Residual error function that calculates the difference between the Bass model output given coefficients
    m, p, q at time t (see below) on the one hand and the actual sales figure on the other hand.

    :param m:       Market potential coefficient
    :param p:       Innovators coefficient
    :param q:       Imitators coefficient
    :param t:       Time
    :param sales:   The actual sales value

    :return: The difference between the calculated Bass function output and the actual provided sales figure
    """
    bass = m * (((p + q) ** 2 / p) * np.exp(-(p + q) * t)) / (1 + (q / p) * np.exp(-(p + q) * t)) ** 2
    return bass - sales


def main() -> None:
    # time intervals
    t = np.linspace(1.0, 10.0, num=10)

    # sales vector
    sales = np.array([840, 1470, 2110, 4000, 7590, 10950, 10530, 9470, 7790, 5890])
    cumulative_sales = np.cumsum(sales)

# residual (error) function
def residual(vars, t, sales):
    M = vars[0]
    P = vars[1]
    Q = vars[2]
    Bass = M * (((P+Q)**2/P)*np.exp(-(P+Q)*t))/(1+(Q/P)*np.exp(-(P+Q)*t))**2
    return (Bass - (sales))

# non linear least square fitting
varfinal,success = leastsq(residual, vars, args=(t, sales))

# estimated coefficients
m = varfinal[0]
p = varfinal[1]
q = varfinal[2]


print(varfinal)
#sales plot (pdf)
#time interpolation
tp=(np.linspace(1.0, 100.0, num=100))/10
cofactor= np.exp(-(p+q) * tp)
sales_pdf= m* (((p+q)**2/p)*cofactor)/(1+(q/p)*cofactor)**2
plt.plot(tp, sales_pdf,t,sales)
plt.title('Sales pdf')
plt.legend(['Fit', 'True'])
plt.show()


# Cumulative sales (cdf)
sales_cdf= m*(1-cofactor)/(1+(q/p)*cofactor)
plt.plot(tp, sales_cdf,t,c_sales)
plt.title('Sales cdf')
plt.legend(['Fit', 'True'])
plt.show()
