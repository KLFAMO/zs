from pmzs_lib import ZeemanSlower
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# Konfiguracja użytkownika
# ============================================================

DATA_FILE = r'C:\svnSr\progs\magnet_zs\ZS_computed_values_v2.txt'

# Dodatkowy shift pola w zakresie 0..300 mm
MAG_SHIFT_MT = 0.0

# Gęsta siatka tylko do rysowania
PLOT_X = list(range(500, -150, -2))

# Używamy tylko par +y / -y
SIDES = ['+y', '-y']

# Parametry startowe do wstępnego fitu:
# [start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1, mrg1,
#  start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2, mrg2]
P0 = [
    0,   140, 50, 50, 90, 0,
    160, 300, 50, 50, 90, 0
]

MIN_R = 25
MAX_R = 50

MIN_BOUNDS = [
    0,   50,  MIN_R, MIN_R, -180, -180,
    50, 100,  MIN_R, MIN_R, -180, -180
]

MAX_BOUNDS = [
    100, 250, MAX_R, MAX_R, 180, 180,
    250, 316, MAX_R, MAX_R, 180, 180
]

BOUNDS = (MIN_BOUNDS, MAX_BOUNDS)

# ----------------------------
# Analiza tolerancji wykonania
# ----------------------------
TOLERANCE_ANALYSIS_ENABLE = True
TOL_DX_MM = 0.4
TOL_DY_MM = 0.4
TOL_DROT_DEG = 0.7

# ----------------------------
# Analiza fizyczna dla 88Sr 1S0-1P1
# ----------------------------
SR88_ANALYSIS_ENABLE = True

# Podaj wartość bezwzględną detuningu lasera od rezonansu zerowego pola.
# Przykład: jeśli pracujesz przy -500 MHz, wpisz 500.0
LASER_DETUNING_MHZ = 500.0

# Parametr nasycenia s = I / I_sat
# np.inf = limit mocnego nasycenia
SATURATION_S = np.inf

# Efektywny współczynnik momentu magnetycznego w jednostkach mu_B.
# Dla 88Sr 1S0(m=0) -> 1P1(m=+1), sigma transition, 1.0 to dobre przybliżenie.
MU_PRIME_FACTOR = 1.0

# Ile najbardziej krytycznych par wypisać
TOP_CRITICAL_PAIRS = 6

# Czy rysować breakdown najbardziej krytycznej pary
PLOT_WORST_PAIR_BREAKDOWN = True

# Czy eksportować finalne pozycje
EXPORT_MAGNETS = False
EXPORT_FILENAME = "magnets_positions_initial_fit.dat"


# ============================================================
# Funkcje pomocnicze
# ============================================================

def load_fit_data(filename):
    """Wczytaj i przygotuj dane do fitu."""
    data_x_raw, data_y_raw = np.loadtxt(
        filename,
        delimiter='\t',
        unpack=True
    )

    fit_x = data_x_raw * 1000.0
    fit_y = data_y_raw / 100.0

    for i, x in enumerate(fit_x):
        if 0 < x < 300:
            fit_y[i] += MAG_SHIFT_MT

    return fit_x, fit_y


def print_fit_summary(label, popt):
    print(f"\n=== {label} ===")
    print("Parametry:")
    print(np.array(popt))


def plot_profile(zs, plot_x, title="Zeeman slower profile"):
    zs.set_sensor(y=0, z=0, data_x=plot_x)
    zs.calc(
        plot=True,
        show_anim=True,
        extra_plots=[],
        direction=0,
        data_x=plot_x
    )
    plt.title(title)
    plt.show()


def plot_tolerance_result(tol_result, fit_y, fit_x):
    """Pokaż nominalny profil i oszacowane pasmo błędu."""
    x = tol_result["x"]
    B0 = tol_result["B0"]
    worst_case = tol_result["worst_case"]
    rss_case = tol_result["rss_case"]

    plt.figure(figsize=(10, 6))
    plt.scatter(fit_x, fit_y, label='Target', zorder=3)
    plt.plot(x, B0, label='Nominal fit')
    plt.fill_between(
        x,
        B0 - rss_case,
        B0 + rss_case,
        alpha=0.25,
        label='Estimated RSS tolerance band'
    )
    plt.fill_between(
        x,
        B0 - worst_case,
        B0 + worst_case,
        alpha=0.15,
        label='Estimated worst-case band'
    )
    plt.xlabel('Distance / mm')
    plt.ylabel('Magnetic field / mT')
    plt.title('Tolerance sensitivity estimate')
    plt.grid(True)
    plt.legend()
    plt.show()

    plt.figure(figsize=(10, 4))
    plt.plot(x, rss_case, label='RSS estimated error')
    plt.plot(x, worst_case, label='Worst-case estimated error')
    plt.xlabel('Distance / mm')
    plt.ylabel('Field error / mT')
    plt.title('Estimated field error due to manufacturing tolerances')
    plt.grid(True)
    plt.legend()
    plt.show()


def compute_quality_metrics(zs, fit_x, fit_y, tol_result=None):
    """
    Proste parametry jakości ZS:
    - Q_nom   : RMS błędu pola nominalnego względem targetu
    - Q_tol   : RMS oszacowanego błędu tolerancyjnego RSS
    - Q_total : połączenie obu
    """
    zs.set_sensor(y=0, z=0, data_x=fit_x)
    B_nom = zs.calc(direction=0, data_x=fit_x)

    Q_nom = np.sqrt(np.mean((B_nom - fit_y) ** 2))

    results = {
        "Q_nom": Q_nom,
        "B_nom": B_nom,
    }

    if tol_result is not None:
        B_tol = tol_result["rss_case"]
        Q_tol = np.sqrt(np.mean(B_tol ** 2))
        Q_total = np.sqrt(Q_nom ** 2 + Q_tol ** 2)

        results["Q_tol"] = Q_tol
        results["Q_total"] = Q_total
        results["max_tol_rss"] = np.max(np.abs(tol_result["rss_case"]))
        results["max_tol_worst"] = np.max(np.abs(tol_result["worst_case"]))

    return results


def print_nominal_quality(quality_nom):
    print("\n=== Parametry jakości nominalnej ===")
    print(f"Q_nom   (RMS nominal fit error) = {quality_nom['Q_nom']:.6f} mT")


def print_tolerance_quality(quality_tol):
    print("\n=== Parametry jakości ZS z tolerancjami ===")
    print(f"Q_nom               = {quality_tol['Q_nom']:.6f} mT")
    print(f"Q_tol   (RMS tol)   = {quality_tol['Q_tol']:.6f} mT")
    print(f"Q_total             = {quality_tol['Q_total']:.6f} mT")
    print(f"max |tol RSS|       = {quality_tol['max_tol_rss']:.6f} mT")
    print(f"max |tol worst|     = {quality_tol['max_tol_worst']:.6f} mT")


# ============================================================
# Główny workflow
# ============================================================

def main():
    # ----------------------------------------
    # 1. Wczytanie danych
    # ----------------------------------------
    fit_x, fit_y = load_fit_data(DATA_FILE)

    dx = np.diff(fit_x)

    print("\n=== DEBUG x-grid ===")
    print("Czy fit_x jest rosnące:", np.all(dx > 0))
    print("Minimalny krok dx [mm]:", np.min(dx))
    print("Maksymalny krok dx [mm]:", np.max(dx))
    print("Czy są powtórzone x:", np.any(dx == 0))

    if np.any(dx == 0):
        dup_idx = np.where(dx == 0)[0]
        print("Indeksy z powtórzonym x:", dup_idx)
        for i in dup_idx:
            print(f"fit_x[{i}]={fit_x[i]}, fit_x[{i+1}]={fit_x[i+1]}")

    print("=== Dane wejściowe ===")
    print(f"Liczba punktów fitu: {len(fit_x)}")
    print(f"Zakres x: {np.min(fit_x):.2f} mm ... {np.max(fit_x):.2f} mm")

    # ----------------------------------------
    # 2. Wstępny fit
    # ----------------------------------------
    zs, popt, pcov = ZeemanSlower.fit_from_data(
        fit_x,
        fit_y,
        SIDES,
        P0,
        BOUNDS
    )

    print_fit_summary("Wynik wstępnego fitu", popt)

    # ----------------------------------------
    # 3. Rysowanie po wstępnym ficie
    # ----------------------------------------
    print("\nRysowanie profilu po wstępnym ficie...")
    zs.set_sensor(y=0, z=0, data_x=PLOT_X)
    zs.calc(
        plot=True,
        show_anim=True,
        extra_plots=[],
        direction=0,
        data_x=PLOT_X
    )

    # ----------------------------------------
    # 4. Parametr jakości nominalnej
    # ----------------------------------------
    quality_nom = compute_quality_metrics(zs, fit_x, fit_y)
    print_nominal_quality(quality_nom)

    # ----------------------------------------
    # 5. Analiza tolerancji wykonania
    # ----------------------------------------
    tol_result = None
    if TOLERANCE_ANALYSIS_ENABLE:
        print("\nUruchamiam analizę tolerancji wykonania...")
        print(f"Założenia: dx=±{TOL_DX_MM} mm, dy=±{TOL_DY_MM} mm, drot=±{TOL_DROT_DEG} deg")

        tol_result = zs.estimate_tolerance_sensitivity(
            data_x=fit_x,
            dx_tol=TOL_DX_MM,
            dy_tol=TOL_DY_MM,
            drot_tol_deg=TOL_DROT_DEG,
            direction=0,
        )

        plot_tolerance_result(tol_result, fit_y, fit_x)

        quality_tol = compute_quality_metrics(zs, fit_x, fit_y, tol_result=tol_result)
        print_tolerance_quality(quality_tol)

        # ----------------------------------------
        # 6. Ranking krytycznych par
        # ----------------------------------------
        critical_pairs = zs.summarize_critical_pairs(
            tol_result,
            top_n=TOP_CRITICAL_PAIRS,
            print_table=True
        )

        if critical_pairs and PLOT_WORST_PAIR_BREAKDOWN:
            worst_pair_index = critical_pairs[0]["pair_index"]
            print(f"\nRysuję breakdown dla najbardziej krytycznej pary: {worst_pair_index}")
            zs.plot_pair_sensitivity_breakdown(tol_result, worst_pair_index)

        # ----------------------------------------
        # 7. Analiza fizyczna dla 88Sr 1S0-1P1
        # ----------------------------------------
        if SR88_ANALYSIS_ENABLE:
            print("\nUruchamiam analizę fizyczną dla 88Sr 1S0-1P1...")

            sr_result = zs.analyze_sr88_1s0_1p1_tolerance(
                tol_result,
                laser_detuning_MHz=LASER_DETUNING_MHZ,
                saturation_s=SATURATION_S,
                mu_prime_factor=MU_PRIME_FACTOR,
            )

            zs.print_sr88_1s0_1p1_report(sr_result)
            zs.plot_sr88_1s0_1p1_report(sr_result)

    # ----------------------------------------
    # 8. Opcjonalny eksport
    # ----------------------------------------
    if EXPORT_MAGNETS:
        zs.export_magnet_positions(EXPORT_FILENAME)

    print("\nGotowe.")


if __name__ == "__main__":
    main()