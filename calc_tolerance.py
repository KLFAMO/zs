from pmzs_lib import ZeemanSlower
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# Konfiguracja
# ============================================================

DATA_FILE = r'C:\svnSr\progs\magnet_zs\ZS_computed_values_v2.txt'

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

# Fine tuning
FINE_TUNE_ENABLE = True
FINE_TUNE_MAX_DELTA_X = 0.5         # mm
FINE_TUNE_MAX_DELTA_Y = 0.5        # mm
FINE_TUNE_MAX_DELTA_ROT_DEG = 1.0   # deg
FINE_TUNE_REGULARIZATION = 0.01

# Analiza tolerancji wykonania
TOLERANCE_ANALYSIS_ENABLE = True
TOL_DX_MM = 0.5
TOL_DY_MM = 0.5
TOL_DROT_DEG = 1.0


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


def plot_final_profile(zs, plot_x, title=None):
    """Narysuj profil na gęstej siatce."""
    zs.set_sensor(y=0, z=0, data_x=plot_x)
    zs.calc(
        plot=True,
        show_anim=True,
        extra_plots=[],
        direction=0,
        data_x=plot_x
    )

    if title is not None:
        plt.title(title)
        plt.show()


def print_fit_summary(label, popt):
    print(f"\n=== {label} ===")
    print("Parametry:")
    print(np.array(popt))


def print_fine_summary(result_fine):
    print("\n=== Wynik fine tuning ===")
    print("success =", result_fine.success)
    print("message =", result_fine.message)
    print("cost    =", result_fine.cost)
    print("x       =", result_fine.x)


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


def summarize_critical_pairs(zs, tol_result, top_n=6):
    """
    Rank +y/-y symmetric magnet pairs by sensitivity.

    Returns list of dicts sorted by total_rss_max descending.
    """
    pairs = tol_result["pairs"]
    err_dx = tol_result["err_dx"]
    err_dy = tol_result["err_dy"]
    err_drot = tol_result["err_drot"]

    results = []

    for k, (idx_plus, idx_minus) in enumerate(pairs):
        e_dx = err_dx[k]
        e_dy = err_dy[k]
        e_drot = err_drot[k]

        total_rss_profile = np.sqrt(e_dx**2 + e_dy**2 + e_drot**2)

        m_plus = zs.magnets[idx_plus]
        m_minus = zs.magnets[idx_minus]

        x_pos = 0.5 * (m_plus.position[0] + m_minus.position[0])
        y_pos = 0.5 * (abs(m_plus.position[1]) + abs(m_minus.position[1]))

        entry = {
            "pair_index": k,
            "idx_plus": idx_plus,
            "idx_minus": idx_minus,
            "x_mm": float(x_pos),
            "y_mm": float(y_pos),
            "max_abs_dx": float(np.max(np.abs(e_dx))),
            "max_abs_dy": float(np.max(np.abs(e_dy))),
            "max_abs_drot": float(np.max(np.abs(e_drot))),
            "rms_dx": float(np.sqrt(np.mean(e_dx**2))),
            "rms_dy": float(np.sqrt(np.mean(e_dy**2))),
            "rms_drot": float(np.sqrt(np.mean(e_drot**2))),
            "total_rss_max": float(np.max(np.abs(total_rss_profile))),
            "total_rss_rms": float(np.sqrt(np.mean(total_rss_profile**2))),
        }
        results.append(entry)

    results.sort(key=lambda d: d["total_rss_max"], reverse=True)

    print("\n=== Najbardziej krytyczne pary magnesów ===")
    print(f"{'rank':>4} {'pair':>4} {'idx+':>5} {'idx-':>5} {'x[mm]':>10} {'|y|[mm]':>10} "
          f"{'max_dx[mT]':>12} {'max_dy[mT]':>12} {'max_drot[mT]':>14} "
          f"{'rss_max[mT]':>12} {'rss_rms[mT]':>12}")

    for rank, item in enumerate(results[:top_n], start=1):
        print(f"{rank:4d} "
              f"{item['pair_index']:4d} "
              f"{item['idx_plus']:5d} "
              f"{item['idx_minus']:5d} "
              f"{item['x_mm']:10.3f} "
              f"{item['y_mm']:10.3f} "
              f"{item['max_abs_dx']:12.4f} "
              f"{item['max_abs_dy']:12.4f} "
              f"{item['max_abs_drot']:14.4f} "
              f"{item['total_rss_max']:12.4f} "
              f"{item['total_rss_rms']:12.4f}")

    return results


def plot_pair_sensitivity_breakdown(tol_result, pair_index):
    """
    Plot dx, dy, drot contributions for one selected pair.
    """
    x = tol_result["x"]
    e_dx = tol_result["err_dx"][pair_index]
    e_dy = tol_result["err_dy"][pair_index]
    e_drot = tol_result["err_drot"][pair_index]
    e_total = np.sqrt(e_dx**2 + e_dy**2 + e_drot**2)

    plt.figure(figsize=(10, 5))
    plt.plot(x, e_dx, label='dx contribution')
    plt.plot(x, e_dy, label='dy contribution')
    plt.plot(x, e_drot, label='drot contribution')
    plt.plot(x, e_total, linewidth=2, label='total RSS')
    plt.xlabel('Distance / mm')
    plt.ylabel('Field error / mT')
    plt.title(f'Sensitivity breakdown for pair {pair_index}')
    plt.grid(True)
    plt.legend()
    plt.show()


def compute_sr88_1S0_1P1_quality_from_field_error(field_error_mT):
    """
    Convert magnetic-field error to detuning error for 88Sr 1S0-1P1.

    Approximation:
    dnu/dB ~ mu_B/h ~ 13.996 MHz/mT
    linewidth ~ 32 MHz
    """
    zeeman_slope_MHz_per_mT = 13.9962449171
    linewidth_MHz = 32.0

    detuning_error_MHz = zeeman_slope_MHz_per_mT * np.abs(field_error_mT)
    q_gamma_profile = detuning_error_MHz / linewidth_MHz

    return {
        "detuning_error_MHz": detuning_error_MHz,
        "Q_gamma_profile": q_gamma_profile,
        "Q_gamma_max": float(np.max(q_gamma_profile)),
        "Q_gamma_rms": float(np.sqrt(np.mean(q_gamma_profile**2))),
    }


def plot_sr88_quality(tol_result, sr_quality):
    plt.figure(figsize=(10, 4))
    plt.plot(tol_result["x"], sr_quality["Q_gamma_profile"])
    plt.xlabel("Distance / mm")
    plt.ylabel("Detuning error / linewidth")
    plt.title("88Sr 1S0-1P1: local tolerance impact in units of linewidth")
    plt.grid(True)
    plt.show()


def print_sr88_quality(sr_quality):
    print("\n=== Interpretacja fizyczna dla 88Sr 1S0-1P1 ===")
    print(f"Max detuning error [MHz] = {np.max(sr_quality['detuning_error_MHz']):.4f}")
    print(f"Q_gamma_max             = {sr_quality['Q_gamma_max']:.4f}")
    print(f"Q_gamma_rms             = {sr_quality['Q_gamma_rms']:.4f}")

    qmax = sr_quality["Q_gamma_max"]
    if qmax < 0.2:
        print("Ocena: bardzo bezpieczny zapas.")
    elif qmax < 0.5:
        print("Ocena: raczej bezpiecznie, wpływ powinien być umiarkowany.")
    elif qmax < 1.0:
        print("Ocena: błąd zaczyna być istotny, lokalnie slowing może być wyraźnie osłabiony.")
    else:
        print("Ocena: lokalny błąd jest porównywalny z linewidth lub większy; to już może realnie psuć pracę ZS.")

# ============================================================
# Główny workflow
# ============================================================

def main():
    # ----------------------------------------
    # 1. Wczytanie danych
    # ----------------------------------------
    fit_x, fit_y = load_fit_data(DATA_FILE)

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
    # 4. Fine tuning
    # ----------------------------------------
    if FINE_TUNE_ENABLE:
        print("\nUruchamiam fine tuning par +y/-y...")

        result_fine = zs.fine_tune_fit(
            data_x=fit_x,
            data_y=fit_y,
            max_delta_x=FINE_TUNE_MAX_DELTA_X,
            max_delta_y=FINE_TUNE_MAX_DELTA_Y,
            max_delta_rot_deg=FINE_TUNE_MAX_DELTA_ROT_DEG,
            direction=0,
            regularization=FINE_TUNE_REGULARIZATION,
            verbose=2,
        )

        print_fine_summary(result_fine)

        print("\nRysowanie profilu po fine tuningu...")
        zs.set_sensor(y=0, z=0, data_x=PLOT_X)
        zs.calc(
            plot=True,
            show_anim=True,
            extra_plots=[],
            direction=0,
            data_x=PLOT_X
        )

    # ----------------------------------------
    # 5. Parametr jakości nominalnej
    # ----------------------------------------
    quality_nom = compute_quality_metrics(zs, fit_x, fit_y)

    print("\n=== Parametry jakości ZS ===")
    print(f"Q_nom   (RMS nominal fit error) = {quality_nom['Q_nom']:.6f} mT")

    # ----------------------------------------
    # 6. Analiza tolerancji wykonania
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

        print("\n=== Parametry jakości ZS z tolerancjami ===")
        print(f"Q_nom               = {quality_tol['Q_nom']:.6f} mT")
        print(f"Q_tol   (RMS tol)   = {quality_tol['Q_tol']:.6f} mT")
        print(f"Q_total             = {quality_tol['Q_total']:.6f} mT")
        print(f"max |tol RSS|       = {quality_tol['max_tol_rss']:.6f} mT")
        print(f"max |tol worst|     = {quality_tol['max_tol_worst']:.6f} mT")

        # ----------------------------------------
        # 7. Ranking krytycznych par
        # ----------------------------------------
        critical_pairs = summarize_critical_pairs(zs, tol_result, top_n=6)

        if critical_pairs:
            worst_pair_index = critical_pairs[0]["pair_index"]
            print(f"\nRysuję breakdown dla najbardziej krytycznej pary: {worst_pair_index}")
            plot_pair_sensitivity_breakdown(tol_result, worst_pair_index)

        # ----------------------------------------
        # 8. Interpretacja fizyczna dla 88Sr 1S0-1P1
        # ----------------------------------------
        sr_quality = compute_sr88_1S0_1P1_quality_from_field_error(tol_result["rss_case"])
        print_sr88_quality(sr_quality)
        plot_sr88_quality(tol_result, sr_quality)

    # ----------------------------------------
    # 9. Opcjonalny eksport
    # ----------------------------------------
    # zs.export_magnet_positions()

    print("\nGotowe.")


if __name__ == "__main__":
    main()