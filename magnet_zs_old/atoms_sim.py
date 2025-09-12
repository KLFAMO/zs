import numpy as np
from scipy.integrate import odeint
from scipy.interpolate import interp1d
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_excel('pomiar_ZS.xlsx',
    sheet_name = 'zs pelny',
    usecols=[0,2],
    nrows=29
)
d.dropna(inplace=True)

z = d.iloc[:, 0].values * 1e-3
B = d.iloc[:, 1].values
interp_fun = interp1d(
    z, B, 
    kind='linear', 
    fill_value="extrapolate"
)

gamma = 32e6
Gamma = 2*np.pi*gamma
lam = 461e-9
epsilon = 0.6
h_bar = 1.054571817e-34
mu_b =  9.74e-24
m = 87.90561*1.66e-27
k = 2*np.pi/lam
S = 1.5
A = h_bar*k*Gamma/(2*m)
C = 4/(Gamma**2)
delta_0 = -2*np.pi*500e6
mu_bohr = 9.274e-24
v_0 = 200



def Bz(z):
    return -interp_fun(z)/100000  # T

def a(v, z):
    return -A * S / (1 + S + C * (delta_0 + k * v - mu_b * Bz(z)/h_bar)**2)

# Funkcja do rozwiązania równania różniczkowego dv/dz = f(v, z)
def dv_dz(v, z):
    return a(v, z)

z_sym = np.arange(0, 0.280, 0.0001)

# Rozwiązywanie równania różniczkowego
v_sym = odeint(dv_dz, v_0, z_sym)

B = [Bz(i) for i in z_sym]

fig, ax1 = plt.subplots()
ax1.plot(z_sym, B, 'g-')
ax1.set_xlabel('z [m]')
ax1.set_ylabel('B [T]', color='g')
ax2 = ax1.twinx()

ax2.plot(z_sym, v_sym, 'b-') 
ax2.set_ylabel('v [m/s]', color='b')

plt.show()
