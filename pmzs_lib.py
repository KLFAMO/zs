import magpylib as mgp
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.optimize import least_squares


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