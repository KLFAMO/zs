import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

def import_ref():
    d = pd.read_csv("ZS_computed_values.txt", sep='\t')
    z =  d.iloc[:, 0].values
    B = d.iloc[:, 1].values * (-1)
    return z, B

def import_meas():
    d = pd.read_excel('pomiar_ZS.xlsx',
        sheet_name = 'zs pelny', usecols=[0, 2], nrows=29,
        #sheet_name = 'ZS_computed_values', usecols=[0,3], usecols=[0,2],  
    )
    d.dropna(inplace=True)
    z =  d.iloc[:, 0].values * 1e-3
    B = d.iloc[:, 1].values * (-1)
    #odwracanie
    # z= 0.28 - z
    # B = B * (-1)
    return z, B

z, B = import_ref()
# z, B = import_meas()


fig, (ax1, ax2) = plt.subplots(2, gridspec_kw={'height_ratios': [1, 3]})
ax1.scatter(z,B)
#plt.show()
interp_fun = interp1d(
    z, B, 
    kind='linear', 
    fill_value="extrapolate"
)

mu_bohr = 9.274e-24
gamma = 32e6
Gamma = 2*np.pi*gamma
lam = 461e-9
epsilon = 0.6 #0.6
h_bar = 1.054571817e-34
mu_b = mu_bohr
m = 87.90561*1.66e-27
k = 2*np.pi/lam
S = 1.0 #1.5
A = h_bar*k*Gamma/(2*m)
C = 4/(Gamma**2)
delta_0 = -2*np.pi*535e6


def Bz(z):
    return -interp_fun(z)/100000  # T

def a(v, z):
    return -A * S / (1 + S + C * (delta_0 + k * v - mu_b * Bz(z)/h_bar)**2)


def simulate(v_0):

    z_sym = 0
    v_sym = v_0
    t_sym = 0
    dt = 0.00001
    z_tab = []
    v_tab = []

    while z_sym < 0.37 and t_sym < 0.01:
        z_tab.append(z_sym)
        v_tab.append(v_sym)

        t_sym = t_sym + dt
        a_sym = a(v_sym, z_sym)
        z_sym = z_sym + a_sym*dt*dt/2 + v_sym*dt
        v_sym = v_sym + a_sym*dt
    
    ax2.plot(z_tab, v_tab, label=f"v_0={v_0} m/s") 


for v_init in [ 100, 200, 300, 400, 450, 500]:
    simulate(v_init)

plt.legend()
plt.show()
