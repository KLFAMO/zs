import magpylib as mgp
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.optimize import least_squares
from scipy import constants as const

class Magnet:
    def __init__(self, name='magnet', size=(13,25,25), position=(0,0,0), rotation=(0,0,0)):
        self.name = name
        self.position = tuple(float(v) for v in position)   # mm
        self.size = tuple(float(v) for v in size)           # mm
        self.rotation = tuple(float(v) for v in rotation)   # rotvec in deg
    
class ZeemanSlower():
    def __init__(self, data_x, data_y, dimension=(13,25,25)):
        self.mgp_objects=[]
        self.magnets = []
        self.max_length=300
        self.external_pipe_diameter=22
        self.data_x = data_x
        self.data_y = data_y
        self.set_sensor()
        self.dimension=dimension
    
    def set_sensor(self, y=0, z=0, data_x=None):
        self.sensor = mgp.Sensor(position=(0, y, z), style_size=1.8)
        if data_x is None:
            data_x = self.data_x
        self.sensor.position = [ (i, y, z) for i in data_x]

    def add_magnets_vector(self, start_x=0, start_r=40, stop_r=40,
                           stop_x=300, number=4,  side='+y', magnets_rotation=0, mrg=0):
        xs = np.linspace(start_x, stop_x, number)
        d = (stop_r-start_r)/(stop_x-start_x)
        for i, x in enumerate(xs):
            if side=='+y':
                pos = (start_r+(x-start_x)*d, 0)
                rot = (0, 0, magnets_rotation+i*mrg)
            elif side == '-y': 
                rot = (0, 0, -magnets_rotation-i*mrg)
                pos =( -start_r-(x-start_x)*d, 0)
            elif side == '+z': 
                rot = (0, -magnets_rotation-i*mrg, 0)
                pos=( 0, start_r+(x-start_x)*d)
            elif side == '-z': 
                rot = (0, magnets_rotation+i*mrg, 0)
                pos=( 0, -start_r-(x-start_x)*d)
            cube=mgp.magnet.Cuboid(
                magnetization=(1100, 0, 0),
                dimension=self.dimension,
                position=(x, *pos)
            )
            # cube.rotate_from_rotvec(np.deg2rad(rot))
            cube.rotate_from_rotvec(rot)
            self.mgp_objects.append(cube)
            # self.magnets.append(Magnet(position=(x, *pos), rotation=tuple([x*rad2deg for x in rot])))
            self.magnets.append(Magnet(position=(x, *pos), rotation=rot))
    
    def add_magnets_cone(self, start_x=0, start_r=40, stop_r=40,
                         stop_x=300, number=4, magnets_rotation=0, mrg=0,
                        sides=['+y','-y','+z','-z']):
        for i in sides:
            self.add_magnets_vector(start_x=start_x, start_r=start_r, stop_r=stop_r,
                stop_x=stop_x, number=number, magnets_rotation=magnets_rotation, mrg=mrg, side=i
            )

    def show(self, top_view=False):
        if top_view:
            fig = mgp.show(self.mgp_objects, self.sensor, style_path_show=False, backend='matplotlib')
            if hasattr(fig, 'axes') and fig.axes:
                fig.axes[0].view_init(elev=90, azim=0)  # Widok z góry
            plt.show()
        else:
            mgp.show(self.mgp_objects, self.sensor, style_path_show=False)

    def plot_field(self, extra_plots=[(0,1), (1,0), (0,2), (2,0)], data_x=None):
        plot_data_x = data_x if data_x is not None else self.data_x
        plt.clf()
        plt.scatter(self.data_x, self.data_y, label='Target')
        plt.plot(plot_data_x, self.B[:,0], label='Simulated')
        if data_x is not None:
            np.savetxt("data/repod/simulated_data_fr.txt", np.column_stack((data_x, self.B[:,0]/1000)), fmt='%10.7f', delimiter='\t', header='x / m\tB / T')
            np.savetxt("data/repod/reference_data_fr.txt", np.column_stack((self.data_x, self.data_y/1000)), fmt='%10.7f', delimiter='\t', header='x / m\tB / T')
        else:
            plt.plot(self.data_x, self.B[:,0], label='(0,0)')
        for i in extra_plots:
            y, z = i
            self.set_sensor(y=y, z=z)
            B_local = self.sensor.getB(self.mgp_objects, sumup=True)
            plt.plot(self.data_x, B_local[:,2], label=str(i))
        
        # plot measurement data
        xm = [
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
            27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47
            ]
        xm = [x*10-88 for x in xm]
        ym = [
            1.7, 0.6, -1.4, -4.3, -9.3, -18.9, -36.0, -61.4, -106.3, -165.3, -219.4, -241.9, -230.2,
              -211.4, -194.3, -167.4, -145.6, -134.3, -117.6, -96.6, -80.1, -57.1, -19.6, 11.5, 31.5, 
              50.4, 77.6, 96.8, 104.9, 121.8, 140.4, 146.7, 162.0, 188.8, 206.5, 220.8, 238.7, 226.1,
                175.4, 104.4, 57.1, 26.5, 11.0, 1.9, -1.6, -3.1, -3.5, -3.4
        ]
        ym = [-y/10 for y in ym]
        ymT = [y/1000 for y in ym]
        xmm = [x/1000 for x in xm]
        plt.scatter(xm, ym, label='Measured')

        # np.savetxt("data/repod/measured_data_fr.txt", np.column_stack((xmm, ymT)), fmt='%10.7f', delimiter='\t', header='x / m\tB / T')
        # end plot measurement data

        plt.legend()
        plt.grid()
        plt.xlabel('Distance / mm')
        plt.ylabel('Magnetic field / mT')
        plt.show()

    def calc(self, show_anim=False, plot=False, extra_plots=[(0,1), (1,0), (0,2), (2,0)],
            direction=0, data_x=None):
        self.B = self.sensor.getB(self.mgp_objects, sumup=True)
        if show_anim:
            self.show(top_view=True)
        if plot:
            if data_x is not None:
                self.set_sensor(y=0, z=0, data_x=data_x)
                self.B = self.sensor.getB(self.mgp_objects, sumup=True)
            self.plot_field(extra_plots=extra_plots, data_x=data_x)
        return self.B[:,direction]
    
    def export_magnet_positions(self, filename='magnets_positions_v2.dat'):
        def normalize_angle(angle):
            """Normalize angle to range [-180, 180], with 0° along +X,
            positive counterclockwise, negative clockwise."""
            angle = (angle + 180) % 360 - 180
            return angle
        
        magnet_data = []
        for idx, magnet in enumerate(self.magnets):
            pos_x, pos_y, pos_z = magnet.position
            rot_x, rot_y, rot_z = magnet.rotation
            # Normalize rotations to [-180, 180] range
            rot_z = normalize_angle(rot_z)
            if pos_y > 0:
                magnet_data.append([pos_x, pos_y, pos_z, rot_x, rot_y, rot_z])
        
        # Sort by Pos_X (column 0)
        magnet_data = sorted(magnet_data, key=lambda row: row[0])
        
        header = "Pos_X(mm)\tPos_Y(mm)\tPos_Z(mm)\tRot_X(deg)\tRot_Y(deg)\tRot_Z(deg)"
        np.savetxt(filename, magnet_data, 
                   fmt='%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f',
                   header=header, comments='')
        
        print(f"\n✓ Plik '{filename}' zapisany pomyślnie!")
        print(f"✓ Liczba magnesów: {len(magnet_data)}")
    
    @classmethod
    def create_from_params(cls, data_x, data_y, sides, params, dimension=(13,25,25), number=4):
        start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1, mrg1, \
        start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2, mrg2 = params

        zs = cls(data_x=data_x, data_y=data_y, dimension=dimension)

        zs.add_magnets_cone(
            start_r=start_r1, stop_r=stop_r1,
            start_x=start_x1, stop_x=stop_x1,
            number=number,
            magnets_rotation=magnets_rotation1,
            mrg=mrg1,
            sides=sides
        )

        zs.add_magnets_cone(
            start_r=start_r2, stop_r=stop_r2,
            start_x=start_x2, stop_x=stop_x2,
            number=number,
            magnets_rotation=magnets_rotation2,
            mrg=mrg2,
            sides=sides
        )

        return zs

    @classmethod
    def fit_from_data(cls, data_x, data_y, sides, p0, bounds, dimension=(13,25,25), number=4):
        def create_zs(start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1, mrg1,
                      start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2, mrg2):
            zs = cls(data_x=data_x, data_y=data_y, dimension=dimension)
            zs.add_magnets_cone(start_r=start_r1, stop_r=stop_r1, start_x=start_x1, stop_x=stop_x1,
                                number=number, magnets_rotation=magnets_rotation1, mrg=mrg1,
                                sides=sides)
            zs.add_magnets_cone(start_r=start_r2, stop_r=stop_r2, start_x=start_x2, stop_x=stop_x2,
                                number=number, magnets_rotation=magnets_rotation2, mrg=mrg2,
                                sides=sides)
            return zs
        
        def fit_fun(data_x, start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1, mrg1,
                    start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2, mrg2):
            zs = create_zs(start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1, mrg1,
                           start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2, mrg2)
            zs.set_sensor(y=0, z=0)
            return zs.calc()
        
        popt, pcov = curve_fit(fit_fun, data_x, data_y, p0=p0, bounds=bounds)
        fitted_zs = create_zs(*popt)
        fitted_zs.set_sensor(y=0, z=0)
        return fitted_zs, popt, pcov
    
    def rebuild_mgp_objects(self):
        """Rebuild Magpylib objects from self.magnets."""
        self.mgp_objects = []

        for mag in self.magnets:
            cube = mgp.magnet.Cuboid(
                magnetization=(1100, 0, 0),
                dimension=mag.size,
                position=mag.position
            )
            # W Twojej wersji i konfiguracji podajesz rotacje w stopniach
            cube.rotate_from_rotvec(mag.rotation)
            self.mgp_objects.append(cube)


    def get_y_symmetric_pairs(self, tol=1e-9):
        """
        Find symmetric pairs only for +y / -y magnets.

        Returns list of tuples:
            [(idx_plus_y, idx_minus_y), ...]

        Conditions:
        - same x
        - same z
        - opposite y
        """
        pairs = []
        used = set()

        for i, m1 in enumerate(self.magnets):
            if i in used:
                continue

            p1 = np.array(m1.position, dtype=float)

            # interesują nas tylko magnesy z y != 0
            if abs(p1[1]) < tol:
                continue

            for j, m2 in enumerate(self.magnets):
                if j <= i or j in used:
                    continue

                p2 = np.array(m2.position, dtype=float)

                cond = (
                    abs(p1[0] - p2[0]) < tol and
                    abs(p1[2] - p2[2]) < tol and
                    abs(p1[1] + p2[1]) < tol and
                    abs(p1[1]) > tol
                )

                if cond:
                    if p1[1] > 0:
                        pairs.append((i, j))
                    else:
                        pairs.append((j, i))
                    used.add(i)
                    used.add(j)
                    break

        return pairs


    def fine_tune_fit(
        self,
        data_x,
        data_y,
        max_delta_x=2.0,
        max_delta_y=1.0,
        max_delta_rot_deg=2.0,
        direction=0,
        pair_tol=1e-9,
        regularization=0.0,
        verbose=2,
    ):
        """
        Fine tuning only for symmetric +y / -y magnet pairs.

        For each pair optimizer fits 3 parameters:
        - dx   : common shift along x [mm]
        - dy   : radial shift in y [mm]
        - drot : symmetric rotation correction around z [deg]

        Applied as:
        +y magnet:
            x += dx
            y += dy
            rot_z += drot

        -y magnet:
            x += dx
            y -= dy
            rot_z -= drot

        Parameters
        ----------
        max_delta_x : float
            Max allowed x shift per pair [mm]
        max_delta_y : float
            Max allowed y shift per pair [mm]
        max_delta_rot_deg : float
            Max allowed z-rotation correction per pair [deg]
        direction : int
            Field component index for calc(direction=...)
        regularization : float
            Optional penalty for large corrections. 0 disables it.
        """

        pairs = self.get_y_symmetric_pairs(tol=pair_tol)

        if not pairs:
            raise RuntimeError("No +y/-y symmetric magnet pairs found.")

        # nominal solution from coarse fit
        base_magnets = [
            Magnet(
                name=m.name,
                size=m.size,
                position=tuple(m.position),
                rotation=tuple(m.rotation),
            )
            for m in self.magnets
        ]

        n_pairs = len(pairs)

        # params per pair: dx, dy, drot
        p0 = np.zeros(3 * n_pairs, dtype=float)

        lower = np.array(
            [-max_delta_x, -max_delta_y, -max_delta_rot_deg] * n_pairs,
            dtype=float
        )
        upper = np.array(
            [ max_delta_x,  max_delta_y,  max_delta_rot_deg] * n_pairs,
            dtype=float
        )

        def apply_pair_params(params):
            """Return new Magnet list after applying pair corrections."""
            new_magnets = [
                Magnet(
                    name=m.name,
                    size=m.size,
                    position=tuple(m.position),
                    rotation=tuple(m.rotation),
                )
                for m in base_magnets
            ]

            for k, (idx_plus, idx_minus) in enumerate(pairs):
                dx, dy, drot = params[3*k:3*k+3]

                m_plus = new_magnets[idx_plus]
                m_minus = new_magnets[idx_minus]

                pos_plus = np.array(m_plus.position, dtype=float)
                pos_minus = np.array(m_minus.position, dtype=float)

                rot_plus = np.array(m_plus.rotation, dtype=float)
                rot_minus = np.array(m_minus.rotation, dtype=float)

                # wspólne przesunięcie w x
                pos_plus[0] += dx
                pos_minus[0] += dx

                # symetryczne przesunięcie w y
                pos_plus[1] += dy
                pos_minus[1] -= dy

                # symetryczna korekta obrotu wokół z
                rot_plus[2] += drot
                rot_minus[2] -= drot

                m_plus.position = tuple(pos_plus)
                m_minus.position = tuple(pos_minus)
                m_plus.rotation = tuple(rot_plus)
                m_minus.rotation = tuple(rot_minus)

            return new_magnets

        def residuals(params):
            trial_magnets = apply_pair_params(params)

            temp_zs = ZeemanSlower(data_x=data_x, data_y=data_y, dimension=self.dimension)
            temp_zs.magnets = trial_magnets
            temp_zs.rebuild_mgp_objects()
            temp_zs.set_sensor(y=0, z=0, data_x=data_x)

            model = temp_zs.calc(direction=direction)
            res = model - data_y

            if regularization > 0:
                reg = regularization * params
                return np.concatenate([res, reg])

            return res

        result = least_squares(
            residuals,
            x0=p0,
            bounds=(lower, upper),
            method='trf',
            verbose=verbose,
        )

        # apply best-fit corrections to current object
        self.magnets = apply_pair_params(result.x)
        self.rebuild_mgp_objects()
        self.set_sensor(y=0, z=0, data_x=data_x)

        return result
    

    def estimate_tolerance_sensitivity(
        self,
        data_x,
        dx_tol=0.5,
        dy_tol=0.5,
        drot_tol_deg=1.0,
        direction=0,
        pair_tol=1e-9,
    ):
        """
        First-order sensitivity estimate for symmetric +y/-y magnet pairs.

        Returns sensitivities of field profile to:
        - pair shift in x
        - pair shift in y
        - pair rotation around z

        Uses central finite differences around the current fitted solution.
        """

        pairs = self.get_y_symmetric_pairs(tol=pair_tol)
        if not pairs:
            raise RuntimeError("No +y/-y symmetric magnet pairs found.")

        base_magnets = [
            Magnet(
                name=m.name,
                size=m.size,
                position=tuple(m.position),
                rotation=tuple(m.rotation),
            )
            for m in self.magnets
        ]

        def calc_profile(magnets):
            temp = ZeemanSlower(data_x=data_x, data_y=np.zeros(len(data_x)), dimension=self.dimension)
            temp.magnets = magnets
            temp.rebuild_mgp_objects()
            temp.set_sensor(y=0, z=0, data_x=data_x)
            return temp.calc(direction=direction)

        def apply_pair_change(pair_idx, dx=0.0, dy=0.0, drot=0.0):
            mags = [
                Magnet(
                    name=m.name,
                    size=m.size,
                    position=tuple(m.position),
                    rotation=tuple(m.rotation),
                )
                for m in base_magnets
            ]

            idx_plus, idx_minus = pairs[pair_idx]

            mp = mags[idx_plus]
            mm = mags[idx_minus]

            pos_p = np.array(mp.position, dtype=float)
            pos_m = np.array(mm.position, dtype=float)
            rot_p = np.array(mp.rotation, dtype=float)
            rot_m = np.array(mm.rotation, dtype=float)

            pos_p[0] += dx
            pos_m[0] += dx

            pos_p[1] += dy
            pos_m[1] -= dy

            rot_p[2] += drot
            rot_m[2] -= drot

            mp.position = tuple(pos_p)
            mm.position = tuple(pos_m)
            mp.rotation = tuple(rot_p)
            mm.rotation = tuple(rot_m)

            return mags

        B0 = calc_profile(base_magnets)

        sens_dx = []
        sens_dy = []
        sens_drot = []

        err_dx = []
        err_dy = []
        err_drot = []

        for k in range(len(pairs)):
            # dB/dx
            Bp = calc_profile(apply_pair_change(k, dx=+dx_tol))
            Bm = calc_profile(apply_pair_change(k, dx=-dx_tol))
            dBdx = (Bp - Bm) / (2.0 * dx_tol)
            sens_dx.append(dBdx)
            err_dx.append(dBdx * dx_tol)

            # dB/dy
            Bp = calc_profile(apply_pair_change(k, dy=+dy_tol))
            Bm = calc_profile(apply_pair_change(k, dy=-dy_tol))
            dBdy = (Bp - Bm) / (2.0 * dy_tol)
            sens_dy.append(dBdy)
            err_dy.append(dBdy * dy_tol)

            # dB/drot
            Bp = calc_profile(apply_pair_change(k, drot=+drot_tol_deg))
            Bm = calc_profile(apply_pair_change(k, drot=-drot_tol_deg))
            dBdrot = (Bp - Bm) / (2.0 * drot_tol_deg)
            sens_drot.append(dBdrot)
            err_drot.append(dBdrot * drot_tol_deg)

        sens_dx = np.array(sens_dx)       # shape: (n_pairs, n_points)
        sens_dy = np.array(sens_dy)
        sens_drot = np.array(sens_drot)

        err_dx = np.array(err_dx)
        err_dy = np.array(err_dy)
        err_drot = np.array(err_drot)

        # Aggregate estimates
        worst_case = (
            np.sum(np.abs(err_dx), axis=0) +
            np.sum(np.abs(err_dy), axis=0) +
            np.sum(np.abs(err_drot), axis=0)
        )

        rss_case = np.sqrt(
            np.sum(err_dx**2, axis=0) +
            np.sum(err_dy**2, axis=0) +
            np.sum(err_drot**2, axis=0)
        )

        return {
            "x": np.array(data_x, dtype=float),
            "B0": B0,
            "pairs": pairs,
            "sens_dx": sens_dx,
            "sens_dy": sens_dy,
            "sens_drot": sens_drot,
            "err_dx": err_dx,
            "err_dy": err_dy,
            "err_drot": err_drot,
            "worst_case": worst_case,
            "rss_case": rss_case,
        }
    

    @staticmethod
    def compute_gradient_profile(x_mm, B_mT):
        """
        Numerical gradient dB/dx with sanitization.

        Input:
            x_mm : position [mm]
            B_mT : magnetic field [mT]

        Output:
            dBdx_mT_per_mm : gradient [mT/mm]

        Note:
            Numerically, 1 mT/mm = 1 T/m
        """
        x_mm = np.asarray(x_mm, dtype=float)
        B_mT = np.asarray(B_mT, dtype=float)

        # keep only finite points
        mask = np.isfinite(x_mm) & np.isfinite(B_mT)
        x = x_mm[mask]
        B = B_mT[mask]

        if len(x) < 3:
            out = np.full_like(x_mm, np.nan, dtype=float)
            return out

        # sort by x
        order = np.argsort(x)
        x_sorted = x[order]
        B_sorted = B[order]

        # remove duplicate x values
        x_unique, unique_idx = np.unique(x_sorted, return_index=True)
        B_unique = B_sorted[unique_idx]

        if len(x_unique) < 3:
            out = np.full_like(x_mm, np.nan, dtype=float)
            return out

        grad_unique = np.gradient(B_unique, x_unique)

        # interpolate gradient back to the original finite points
        grad_interp = np.interp(x, x_unique, grad_unique)

        out = np.full_like(x_mm, np.nan, dtype=float)
        out[mask] = grad_interp
        return out


    @staticmethod
    def sr88_1s0_1p1_constants():
        """
        Constants for 88Sr Zeeman slower on 1S0-1P1 transition (461 nm).

        Returns dict:
            lambda_m
            k
            gamma_hz
            gamma_rad_s
            mass_kg
            muB_J_T
            muB_Hz_T
            zeeman_MHz_per_mT
            a_max_m_s2
        """
        lambda_m = 461e-9
        k = 2.0 * np.pi / lambda_m

        # Natural linewidth ~ 32 MHz for 1S0-1P1 in Sr
        gamma_hz = 32.0e6
        gamma_rad_s = 2.0 * np.pi * gamma_hz

        # 88Sr mass
        mass_kg = 87.9056125 * const.atomic_mass

        muB_J_T = const.physical_constants["Bohr magneton"][0]
        muB_Hz_T = const.physical_constants["Bohr magneton in Hz/T"][0]

        zeeman_MHz_per_mT = muB_Hz_T / 1e9  # MHz/mT

        # Max scattering-limited acceleration for saturated cycling transition
        a_max_m_s2 = const.hbar * k * gamma_rad_s / (2.0 * mass_kg)

        return {
            "lambda_m": lambda_m,
            "k": k,
            "gamma_hz": gamma_hz,
            "gamma_rad_s": gamma_rad_s,
            "mass_kg": mass_kg,
            "muB_J_T": muB_J_T,
            "muB_Hz_T": muB_Hz_T,
            "zeeman_MHz_per_mT": zeeman_MHz_per_mT,
            "a_max_m_s2": a_max_m_s2,
        }


    def summarize_critical_pairs(self, tol_result, top_n=6, print_table=True):
        """
        Rank +y/-y symmetric pairs by sensitivity.

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

            m_plus = self.magnets[idx_plus]
            m_minus = self.magnets[idx_minus]

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

        if print_table:
            print("\n=== Najbardziej krytyczne pary magnesów ===")
            print(f"{'rank':>4} {'pair':>4} {'idx+':>5} {'idx-':>5} "
                  f"{'x[mm]':>10} {'|y|[mm]':>10} "
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


    def plot_pair_sensitivity_breakdown(self, tol_result, pair_index):
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


    def analyze_sr88_1s0_1p1_tolerance(
        self,
        tol_result,
        laser_detuning_MHz=None,
        v_profile_m_s=None,
        saturation_s=np.inf,
        mu_prime_factor=1.0,
        use_absolute_B_for_velocity=True,
    ):
        """
        Full physical tolerance analysis for 88Sr 1S0-1P1 Zeeman slower.

        Parameters
        ----------
        tol_result : dict
            Output of estimate_tolerance_sensitivity(...)
        laser_detuning_MHz : float or None
            Absolute laser detuning from zero-field resonance.
            Example: 500 means |delta_L| = 500 MHz.
            If provided and v_profile_m_s is None, velocity profile is estimated
            from magnetic profile B(x).
        v_profile_m_s : array-like or None
            Explicit resonance velocity profile v(x). If provided, it overrides
            laser_detuning_MHz for adiabaticity calculations.
        saturation_s : float
            Saturation parameter. If inf, assumes fully saturated limit.
        mu_prime_factor : float
            Effective magnetic moment in units of mu_B.
            For sigma transition 1S0(m=0) -> 1P1(m=+1), mu_prime_factor~1 is a
            sensible approximation.
        use_absolute_B_for_velocity : bool
            If True, uses |B| when estimating resonance velocity from field.
            Safer for quick engineering estimates.

        Returns dict with:
            - detuning_error_rss_MHz
            - detuning_error_worst_MHz
            - velocity_error_rss_m_s
            - velocity_error_worst_m_s
            - Q_gamma_rss_profile
            - Q_gamma_worst_profile
            - Q_gamma_rss_max
            - Q_gamma_worst_max
            - dBdx_nom_mT_per_mm
            - dBdx_rss_upper_mT_per_mm
            - dBdx_rss_lower_mT_per_mm
            - dBdx_worst_upper_mT_per_mm
            - dBdx_worst_lower_mT_per_mm
            - delta_dBdx_rss_mT_per_mm
            - delta_dBdx_worst_mT_per_mm
            - Q_grad_rss_max
            - Q_grad_worst_max
            - v_nom_m_s (if available)
            - eta_nom (if available)
            - eta_rss_upper / eta_rss_lower / eta_worst_upper / eta_worst_lower (if available)
            - eta_nom_max / eta_rss_max / eta_worst_max (if available)
        """
        cst = self.sr88_1s0_1p1_constants()

        x = np.asarray(tol_result["x"], dtype=float)
        B0 = np.asarray(tol_result["B0"], dtype=float)
        rss = np.asarray(tol_result["rss_case"], dtype=float)
        worst = np.asarray(tol_result["worst_case"], dtype=float)

        zeeman_MHz_per_mT = mu_prime_factor * cst["zeeman_MHz_per_mT"]
        lambda_m = cst["lambda_m"]
        k = cst["k"]
        gamma_hz = cst["gamma_hz"]
        muB_J_T = cst["muB_J_T"] * mu_prime_factor

        # Effective maximum acceleration with finite saturation
        if np.isinf(saturation_s):
            sat_factor = 1.0
        else:
            sat_factor = saturation_s / (1.0 + saturation_s)

        a_max_eff = cst["a_max_m_s2"] * sat_factor

        # -----------------------------
        # Field-error -> detuning error
        # -----------------------------
        detuning_error_rss_MHz = zeeman_MHz_per_mT * np.abs(rss)
        detuning_error_worst_MHz = zeeman_MHz_per_mT * np.abs(worst)

        Q_gamma_rss_profile = detuning_error_rss_MHz / (gamma_hz / 1e6)
        Q_gamma_worst_profile = detuning_error_worst_MHz / (gamma_hz / 1e6)

        # -----------------------------
        # Field-error -> equivalent velocity error
        # Doppler shift in Hz is v/lambda
        # => dv = dnu * lambda
        # -----------------------------
        velocity_error_rss_m_s = detuning_error_rss_MHz * 1e6 * lambda_m
        velocity_error_worst_m_s = detuning_error_worst_MHz * 1e6 * lambda_m

        # -----------------------------
        # Gradient sensitivity
        # -----------------------------
        dBdx_nom = self.compute_gradient_profile(x, B0)

        dBdx_rss_upper = self.compute_gradient_profile(x, B0 + rss)
        dBdx_rss_lower = self.compute_gradient_profile(x, B0 - rss)

        dBdx_worst_upper = self.compute_gradient_profile(x, B0 + worst)
        dBdx_worst_lower = self.compute_gradient_profile(x, B0 - worst)

        delta_dBdx_rss = np.maximum(
            np.abs(dBdx_rss_upper - dBdx_nom),
            np.abs(dBdx_rss_lower - dBdx_nom)
        )

        delta_dBdx_worst = np.maximum(
            np.abs(dBdx_worst_upper - dBdx_nom),
            np.abs(dBdx_worst_lower - dBdx_nom)
        )

        denom_grad = np.where(
            np.isfinite(dBdx_nom),
            np.maximum(np.abs(dBdx_nom), 1e-12),
            np.nan
        )

        Q_grad_rss_profile = delta_dBdx_rss / denom_grad
        Q_grad_worst_profile = delta_dBdx_worst / denom_grad

        result = {
            "x_mm": x,
            "B0_mT": B0,
            "rss_case_mT": rss,
            "worst_case_mT": worst,

            "detuning_error_rss_MHz": detuning_error_rss_MHz,
            "detuning_error_worst_MHz": detuning_error_worst_MHz,
            "velocity_error_rss_m_s": velocity_error_rss_m_s,
            "velocity_error_worst_m_s": velocity_error_worst_m_s,

            "Q_gamma_rss_profile": Q_gamma_rss_profile,
            "Q_gamma_worst_profile": Q_gamma_worst_profile,
            "Q_gamma_rss_max": float(np.max(Q_gamma_rss_profile)),
            "Q_gamma_worst_max": float(np.max(Q_gamma_worst_profile)),
            "Q_gamma_rss_rms": float(np.sqrt(np.mean(Q_gamma_rss_profile**2))),
            "Q_gamma_worst_rms": float(np.sqrt(np.mean(Q_gamma_worst_profile**2))),

            "dBdx_nom_mT_per_mm": dBdx_nom,
            "dBdx_rss_upper_mT_per_mm": dBdx_rss_upper,
            "dBdx_rss_lower_mT_per_mm": dBdx_rss_lower,
            "dBdx_worst_upper_mT_per_mm": dBdx_worst_upper,
            "dBdx_worst_lower_mT_per_mm": dBdx_worst_lower,

            "delta_dBdx_rss_mT_per_mm": delta_dBdx_rss,
            "delta_dBdx_worst_mT_per_mm": delta_dBdx_worst,

            "Q_grad_rss_profile": Q_grad_rss_profile,
            "Q_grad_worst_profile": Q_grad_worst_profile,
            "Q_grad_rss_max": float(np.nanmax(Q_grad_rss_profile)),
            "Q_grad_worst_max": float(np.nanmax(Q_grad_worst_profile)),
            "Q_grad_rss_rms": float(np.sqrt(np.nanmean(Q_grad_rss_profile**2))),
            "Q_grad_worst_rms": float(np.sqrt(np.nanmean(Q_grad_worst_profile**2))),

            "a_max_eff_m_s2": float(a_max_eff),
            "mu_prime_factor": float(mu_prime_factor),
            "saturation_s": float(saturation_s) if not np.isinf(saturation_s) else np.inf,
        }

        # -----------------------------
        # Optional adiabaticity estimate
        # -----------------------------
        def velocity_from_B_profile(B_profile_mT, detuning_MHz):
            B_used = np.abs(B_profile_mT) if use_absolute_B_for_velocity else B_profile_mT
            zeeman_hz = zeeman_MHz_per_mT * 1e6 * B_used
            detuning_hz = abs(detuning_MHz) * 1e6
            v = lambda_m * np.maximum(detuning_hz - zeeman_hz, 0.0)
            return v

        def required_acceleration(v_profile, dBdx_mT_per_mm):
            # 1 mT/mm numerically equals 1 T/m
            grad_T_per_m = np.abs(dBdx_mT_per_mm)
            return np.abs(v_profile) * muB_J_T * grad_T_per_m / (const.hbar * k)

        v_nom = None
        if v_profile_m_s is not None:
            v_nom = np.asarray(v_profile_m_s, dtype=float)
        elif laser_detuning_MHz is not None:
            v_nom = velocity_from_B_profile(B0, laser_detuning_MHz)

        if v_nom is not None:
            if len(v_nom) != len(x):
                raise ValueError(
                    f"v_profile_m_s length {len(v_nom)} does not match profile length {len(x)}"
                )

            a_req_nom = required_acceleration(v_nom, dBdx_nom)
            eta_nom = a_req_nom / a_max_eff

            if laser_detuning_MHz is not None:
                v_rss_upper = velocity_from_B_profile(B0 + rss, laser_detuning_MHz)
                v_rss_lower = velocity_from_B_profile(B0 - rss, laser_detuning_MHz)
                v_worst_upper = velocity_from_B_profile(B0 + worst, laser_detuning_MHz)
                v_worst_lower = velocity_from_B_profile(B0 - worst, laser_detuning_MHz)
            else:
                # if external v(x) is provided, keep same v for perturbed profiles
                v_rss_upper = v_nom
                v_rss_lower = v_nom
                v_worst_upper = v_nom
                v_worst_lower = v_nom

            a_req_rss_upper = required_acceleration(v_rss_upper, dBdx_rss_upper)
            a_req_rss_lower = required_acceleration(v_rss_lower, dBdx_rss_lower)
            a_req_worst_upper = required_acceleration(v_worst_upper, dBdx_worst_upper)
            a_req_worst_lower = required_acceleration(v_worst_lower, dBdx_worst_lower)

            eta_rss_upper = a_req_rss_upper / a_max_eff
            eta_rss_lower = a_req_rss_lower / a_max_eff
            eta_worst_upper = a_req_worst_upper / a_max_eff
            eta_worst_lower = a_req_worst_lower / a_max_eff

            eta_rss_envelope = np.maximum(eta_rss_upper, eta_rss_lower)
            eta_worst_envelope = np.maximum(eta_worst_upper, eta_worst_lower)

            result.update({
                "v_nom_m_s": v_nom,
                "eta_nom": eta_nom,
                "eta_rss_upper": eta_rss_upper,
                "eta_rss_lower": eta_rss_lower,
                "eta_worst_upper": eta_worst_upper,
                "eta_worst_lower": eta_worst_lower,
                "eta_rss_envelope": eta_rss_envelope,
                "eta_worst_envelope": eta_worst_envelope,

                "eta_nom_max": float(np.max(eta_nom)),
                "eta_rss_max": float(np.max(eta_rss_envelope)),
                "eta_worst_max": float(np.max(eta_worst_envelope)),

                "eta_nom_rms": float(np.sqrt(np.mean(eta_nom**2))),
                "eta_rss_rms": float(np.sqrt(np.mean(eta_rss_envelope**2))),
                "eta_worst_rms": float(np.sqrt(np.mean(eta_worst_envelope**2))),
            })

        return result


    def print_sr88_1s0_1p1_report(self, sr_result):
        """
        Human-readable report for 88Sr 1S0-1P1 tolerance analysis.
        """
        print("\n=== 88Sr 1S0-1P1: raport fizyczny ===")
        print(f"a_max_eff [m/s^2]            = {sr_result['a_max_eff_m_s2']:.3e}")
        print(f"Q_gamma_rss_max              = {sr_result['Q_gamma_rss_max']:.4f}")
        print(f"Q_gamma_worst_max            = {sr_result['Q_gamma_worst_max']:.4f}")
        print(f"Q_grad_rss_max               = {sr_result['Q_grad_rss_max']:.4f}")
        print(f"Q_grad_worst_max             = {sr_result['Q_grad_worst_max']:.4f}")

        print(f"max detuning RSS [MHz]       = {np.max(sr_result['detuning_error_rss_MHz']):.4f}")
        print(f"max detuning worst [MHz]     = {np.max(sr_result['detuning_error_worst_MHz']):.4f}")

        print(f"max dv RSS [m/s]             = {np.max(sr_result['velocity_error_rss_m_s']):.4f}")
        print(f"max dv worst [m/s]           = {np.max(sr_result['velocity_error_worst_m_s']):.4f}")

        print(f"max |dB/dx| nominal [mT/mm]  = {np.max(np.abs(sr_result['dBdx_nom_mT_per_mm'])):.4f}")
        print(f"max Δ(dB/dx) RSS [mT/mm]     = {np.max(sr_result['delta_dBdx_rss_mT_per_mm']):.4f}")
        print(f"max Δ(dB/dx) worst [mT/mm]   = {np.max(sr_result['delta_dBdx_worst_mT_per_mm']):.4f}")

        if "eta_nom_max" in sr_result:
            print(f"eta_nom_max                  = {sr_result['eta_nom_max']:.4f}")
            print(f"eta_rss_max                  = {sr_result['eta_rss_max']:.4f}")
            print(f"eta_worst_max                = {sr_result['eta_worst_max']:.4f}")

            if sr_result["eta_worst_max"] < 0.5:
                print("Ocena adiabatyczności: bardzo bezpieczny zapas.")
            elif sr_result["eta_worst_max"] < 0.7:
                print("Ocena adiabatyczności: wciąż sensowny zapas.")
            elif sr_result["eta_worst_max"] < 1.0:
                print("Ocena adiabatyczności: działa, ale margines robi się mały.")
            else:
                print("Ocena adiabatyczności: lokalnie wymagane opóźnienie przekracza limit rozpraszania.")
        else:
            print("Eta nie policzono: podaj laser_detuning_MHz albo v_profile_m_s.")

        # Quick engineering interpretation
        qg = sr_result["Q_gamma_worst_max"]
        qgrad = sr_result["Q_grad_worst_max"]

        if qg < 0.2:
            txt_res = "bardzo mały wpływ błędu pola na rezonans"
        elif qg < 0.5:
            txt_res = "umiarkowany wpływ błędu pola na rezonans"
        elif qg < 1.0:
            txt_res = "wyraźny wpływ błędu pola na rezonans"
        else:
            txt_res = "silny wpływ błędu pola; lokalnie można wypaść z linewidth"

        if qgrad < 0.1:
            txt_grad = "gradient bardzo stabilny"
        elif qgrad < 0.3:
            txt_grad = "gradient zmienia się umiarkowanie"
        elif qgrad < 0.5:
            txt_grad = "gradient robi się istotnie wrażliwy"
        else:
            txt_grad = "gradient jest mocno wrażliwy na tolerancje"

        print(f"Interpretacja rezonansu: {txt_res}")
        print(f"Interpretacja gradientu: {txt_grad}")


    def plot_sr88_1s0_1p1_report(self, sr_result):
        """
        Plot physical tolerance diagnostics for 88Sr 1S0-1P1.
        """
        x = sr_result["x_mm"]

        # Q_gamma
        plt.figure(figsize=(10, 4))
        plt.plot(x, sr_result["Q_gamma_rss_profile"], label='Q_gamma RSS')
        plt.plot(x, sr_result["Q_gamma_worst_profile"], label='Q_gamma worst')
        plt.xlabel("Distance / mm")
        plt.ylabel("Detuning error / linewidth")
        plt.title("88Sr 1S0-1P1: resonance error in units of linewidth")
        plt.grid(True)
        plt.legend()
        plt.show()

        # Velocity-equivalent error
        plt.figure(figsize=(10, 4))
        plt.plot(x, sr_result["velocity_error_rss_m_s"], label='dv RSS')
        plt.plot(x, sr_result["velocity_error_worst_m_s"], label='dv worst')
        plt.xlabel("Distance / mm")
        plt.ylabel("Equivalent velocity error / m/s")
        plt.title("88Sr 1S0-1P1: equivalent resonance velocity error")
        plt.grid(True)
        plt.legend()
        plt.show()

        # Gradient error
        plt.figure(figsize=(10, 4))
        plt.plot(x, sr_result["Q_grad_rss_profile"], label='Q_grad RSS')
        plt.plot(x, sr_result["Q_grad_worst_profile"], label='Q_grad worst')
        plt.xlabel("Distance / mm")
        plt.ylabel("Relative gradient error")
        plt.title("88Sr 1S0-1P1: relative gradient sensitivity")
        plt.grid(True)
        plt.legend()
        plt.show()

        # Eta if available
        if "eta_nom" in sr_result:
            plt.figure(figsize=(10, 5))
            plt.plot(x, sr_result["eta_nom"], label='eta nominal')
            plt.plot(x, sr_result["eta_rss_envelope"], label='eta RSS envelope')
            plt.plot(x, sr_result["eta_worst_envelope"], label='eta worst envelope')
            plt.axhline(1.0, linestyle='--', linewidth=1, label='eta=1 limit')
            plt.xlabel("Distance / mm")
            plt.ylabel("eta = a_required / a_max")
            plt.title("88Sr 1S0-1P1: adiabaticity / slowing margin")
            plt.grid(True)
            plt.legend()
            plt.show()