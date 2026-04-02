import matplotlib.pyplot as plt
import numpy as np

data_x, data_y = np.loadtxt('data/dane_ZS_trapping_area.txt', unpack=True)

data_x = data_x + 290

x = np.array(data_x)
y = np.array(data_y)

# zakres do fitu
mask = (x >= 370) & (x <= 380)
x_fit = x[mask]
y_fit = y[mask]

# fit + macierz kowariancji
(p, cov) = np.polyfit(x_fit, y_fit, 1, cov=True)
a, b = p

# niepewności (sqrt z diagonalnych elementów macierzy)
a_err = np.sqrt(cov[0, 0])
b_err = np.sqrt(cov[1, 1])

print(f"a = {a} ± {a_err}")
print(f"b = {b} ± {b_err}")

# linia fitu (ładna, gładka)
x_line = np.linspace(min(x_fit), max(x_fit), 100)
y_line = a * x_line + b

# wykres
plt.scatter(data_x, data_y, color='orange', label='measured')
plt.plot(x_line, y_line, color='black', linewidth=1,
         label=f'fit')

plt.grid()
plt.xlim(370, 380)
plt.ylim(-0.1, 0.075)
plt.legend()
plt.show()