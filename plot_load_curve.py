import matplotlib.pyplot as plt
import numpy as np

# Import data from data/
# data_x, data_y = np.loadtxt('data/ladowanie3_2023_12_18.txt', delimiter='\t', unpack=True)
# plt.plot(data_x, (data_y + 0.0535)*100, label='Dane eksperymentalne')
# plt.xlabel('Time [s]')
# plt.ylabel('Number of atoms [a.u.]')
# plt.grid()
# plt.show()

data_x, data_y = np.loadtxt('data/540-500_fit.txt', delimiter='\t', unpack=True)
data_x = data_x + 2.636
data_y = (data_y + 0.052)*100*2
dfx = data_x[25:-1]
dfy = data_y[25:-1]
print(dfx)
print(dfy)

# fit to exponential
def exp_func(x, a, b, c):
    return a * (1 - np.exp(-b * x)) + c
from scipy.optimize import curve_fit
popt, pcov = curve_fit(exp_func, dfx, dfy, p0=[100, 0.1, 0])
print("Fitted parameters:", popt)
# plot fit
x_fit = np.linspace(0, max(dfx), 100)
y_fit = exp_func(x_fit, *popt)
print("Fitted parameters: ", popt)

plt.scatter(data_x, data_y , label='Measurement', s=6)
plt.plot(x_fit, y_fit, 'r-', label='Exponential fit')

# export fit and data to txt to repod
# np.savetxt('data/repod/load_curve_fit.txt', np.column_stack((x_fit, y_fit*1e8)), delimiter='\t')
# np.savetxt('data/repod/load_curve_meas.txt', np.column_stack((data_x, data_y*1e8)), delimiter='\t')

plt.xlabel('Time / s')
plt.ylabel('Number of atoms / $10^8$')
plt.grid()
plt.legend()
plt.show()