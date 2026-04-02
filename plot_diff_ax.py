import matplotlib.pyplot as plt
import numpy as np

# load data: first column - position, column 2,3,4,5 - separate series of measurements
data = np.loadtxt('data/dane_Bfield_gora_dol.txt', unpack=True)

# data_x, data_y = np.loadtxt('data/dane_Bfield_gora_dol.txt', unpack=True)

print (data)
# print (data_y)

data_x = data[0]
data_1 = data[1]
data_2 = data[2]
data_3 = data[3]   
data_4 = data[4]
data_5 = data[5]



plt.scatter(data_x, data_2, color='orange', label='-1.5 mm')  
plt.scatter(data_x, data_3, color='green', label='-2.5 mm')
plt.plot(data_x, data_1, color='blue', label='0 mm', dashes=(5, 2))
plt.scatter(data_x, data_4, color='red', label='+1.5 mm')
plt.scatter(data_x, data_5, color='purple', label='+2.5 mm')
plt.legend()
plt.grid()

plt.show()