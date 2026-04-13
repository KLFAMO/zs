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
    
    

data_x, data_y = np.loadtxt('C:\svnSr\progs\magnet_zs\ZS_computed_values_v2.txt', delimiter='\t', unpack=True)
data_x = data_x*1000
data_y = data_y/100
mag_shift = 0  # mT
for i, v in enumerate(data_x):
    if 0<data_x[i]<300:
        data_y[i] += mag_shift

sides = [#'+z','-z',
         '+y','-y'
         ]

p0 = [0, 140, 50, 50, 90, 00,
      160, 300, 50, 50, 90, 0]

min_r = 25
min_bounds = [0,   50,  min_r, min_r, -180, -180,
              50, 100,  min_r, min_r, -180, -180]

max_r = 50
max_bounds = [100, 250, max_r, max_r,  180,  180,
              250, 316, max_r, max_r,  180,  180]

bounds = (min_bounds, max_bounds)

# zs_test = ZeemanSlower.create_from_params(data_x, data_y, sides, p0, dimension=(13,25,25), number=4)
# zs_test.set_sensor(y=0, z=0)
# zs_test.calc(plot=True, show_anim=True)

zs, popt, pcov = ZeemanSlower.fit_from_data(data_x, data_y, sides, p0, bounds)


# Fine-tune individual magnet positions
# # popt_fine, pcov_fine = zs.fine_tune_fit(data_x, data_y, max_delta_pos=5.0, max_delta_rot_deg=5.0)
zs.set_sensor(y=0, z=0)
data_x = list(range(500, -150, -2))
zs.calc(
        plot=True, 
        show_anim=True, 
        # extra_plots=[(0, 1), (1,0), (-1, 0), (0,-1)], 
        extra_plots=[],
        direction=0, 
        data_x=data_x
        )
# print([x.position[0] for x in zs.magnets])
# print(popt)
#print(zs.B)

# Export magnet positions and rotations to file
# zs.export_magnet_positions()

# for i in zs.magnets:
#     i.fc_draw()
