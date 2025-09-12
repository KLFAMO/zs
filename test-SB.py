import numpy as np
import matplotlib.pyplot as plt
import magpylib as magpy
import numpy.polynomial.polynomial as poly
from scipy import optimize
# 1. define sources and observers as objects
a=50
b=30
c=50
d=0.05
e=0.099
def cube_calculation(xi,yi,zi):
    return magpy.magnet.Cuboid(magnetization=(0,1260,0), dimension=(a,b,c), position=(xi,yi,zi))

xi_number = 10 #liczba kostek
xi_stamp = 45.3 #odleglosc miedzy kostkami
xi_list = np.linspace(20,xi_number*xi_stamp,xi_number)

wi_number = 3
wi_stamp = 42.3
wi_list = np.linspace(20,wi_number*wi_stamp,wi_number)

cube_vector1 = [] #iksowe kostki
for xi in xi_list:
    cube = cube_calculation(xi+10,xi*d+120,0) #polozenie kostki
    cube.rotate_from_rotvec((0,0,45), degrees=True) #rotacja kostki
    cube_vector1.append(cube)

cube_vector2 = [] #igrekowe kostki
for xi in xi_list:
    cube = cube_calculation(xi+10,-xi*d-120,0)
    cube.rotate_from_rotvec((0,0,-225), degrees=True)
    cube_vector2.append(cube)

##cube_vector3 = [] #drugi rzad kostki
##for wi in wi_list:
##    cube = cube_calculation(wi+193,-wi*e+90,0)
##    cube.rotate_from_rotvec((0,0,45), degrees=True)
##    cube_vector3.append(cube)
##
##cube_vector4 = [] #drugi rzad kostki
##for wi in wi_list:
##    cube = cube_calculation(wi+193,wi*e-90,0)
##    cube.rotate_from_rotvec((0,0,-225), degrees=True)
##    cube_vector4.append(cube)        
    
cube_vector = cube_vector1 + cube_vector2 #+ cube_vector3 + cube_vector4

#definicja sensora
sensor = magpy.Sensor(position=(0,0,0), style_size=1.8)
sensor.position = np.linspace((0,0,0), (400,0,0), 200)

#animacja
magpy.show(cube_vector, sensor, backend='plotly', animation=2, style_path_show=False)

# 3. compute field at sensor (and plot with Matplotlib)
B = sensor.getB(cube_vector, sumup=True)

X, Y = np.loadtxt('ZS_computed_values.txt', delimiter='\t', unpack=True)

##def func(X, cube_calculation):
##    y = cube_calculation
##    #return y
##
##alpha, beta = optimize.curve_fit(func, xdata = X, ydata = Y)[0]
##print(f'alpha={alpha}, beta={beta}')

#wyswietlanie
plt.plot(B, label=['Bx', 'By', 'Bz'])
plt.scatter(X*1000/1.5, Y/100, label=['B_field'])
##plt.plot(X, cube_calculation), 'r'
plt.legend()
plt.grid(color='.8')
plt.show()




