import matplotlib.pyplot as plt
import numpy as np

data_x, data_y = np.loadtxt('data/dane_ZS_trapping_area.txt', unpack=True)

data_x = data_x + 290

plt.scatter(data_x, data_y, color='orange')
# plt.xlabel('X-axis Label')
# plt.ylabel('Y-axis Label')
# plt.title('Trap Area Measurement')
plt.grid()
plt.xlim(370, 380)
plt.ylim(-0.1, 0.075)
# plt.legend()
plt.show()