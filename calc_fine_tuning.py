from pmzs_lib import ZeemanSlower
import numpy as np


data_x_raw, data_y_raw = np.loadtxt(
    'C:\\svnSr\\progs\\magnet_zs\\ZS_computed_values_v2.txt',
    delimiter='\t',
    unpack=True
)

# ----------------------------------------
# Dane do fitu
# ----------------------------------------
fit_x = data_x_raw * 1000.0
fit_y = data_y_raw / 100.0

mag_shift = 0  # mT
for i, x in enumerate(fit_x):
    if 0 < x < 300:
        fit_y[i] += mag_shift

# ----------------------------------------
# Gęsta siatka tylko do rysowania
# ----------------------------------------
plot_x = list(range(500, -150, -2))

sides = [
    # '+z', '-z',
    '+y', '-y'
]

p0 = [
    0,   140, 50, 50, 90, 0,
    160, 300, 50, 50, 90, 0
]

min_r = 25
min_bounds = [
    0,   50,  min_r, min_r, -180, -180,
    50, 100,  min_r, min_r, -180, -180
]

max_r = 50
max_bounds = [
    100, 250, max_r, max_r, 180, 180,
    250, 316, max_r, max_r, 180, 180
]

bounds = (min_bounds, max_bounds)

# ----------------------------------------
# 1. Wstępny fit na danych pomiarowych
# ----------------------------------------
zs, popt, pcov = ZeemanSlower.fit_from_data(
    fit_x,
    fit_y,
    sides,
    p0,
    bounds
)

print("=== Wynik wstępnego fitu ===")
print("popt =", popt)

# ----------------------------------------
# 2. Rysowanie po wstępnym ficie na gęstej siatce
# ----------------------------------------
zs.set_sensor(y=0, z=0, data_x=plot_x)
zs.calc(
    plot=True,
    show_anim=True,
    extra_plots=[],
    direction=0,
    data_x=plot_x
)

# ----------------------------------------
# 3. Fine tuning na danych pomiarowych
# ----------------------------------------
result_fine = zs.fine_tune_fit(
    data_x=fit_x,
    data_y=fit_y,
    max_delta_x=15.0,         # mm
    max_delta_y=15.0,         # mm
    max_delta_rot_deg=20.0,  # deg
    direction=0,
    regularization=0.01,
    verbose=2,
)

print("\n=== Wynik fine tuning ===")
print("success =", result_fine.success)
print("message =", result_fine.message)
print("cost =", result_fine.cost)
print("x =", result_fine.x)

# ----------------------------------------
# 4. Rysowanie po fine tuningu na gęstej siatce
# ----------------------------------------
zs.set_sensor(y=0, z=0, data_x=plot_x)
zs.calc(
    plot=True,
    show_anim=True,
    extra_plots=[],
    direction=0,
    data_x=plot_x
)

# ----------------------------------------
# 5. Opcjonalnie: wypisz pozycje magnesów
# ----------------------------------------
print("\nPozycje x magnesów:")
print([m.position[0] for m in zs.magnets])

# ----------------------------------------
# 6. Opcjonalnie: eksport
# ----------------------------------------
# zs.export_magnet_positions()