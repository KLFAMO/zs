import magpylib as mgp
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

class ZeemanSlower():
    def __init__(self, data_x, data_y, dimension=(13,25,25)):
        self.objects=[]
        self.max_length=300
        self.external_pipe_diameter=22
        self.data_x = data_x
        self.data_y = data_y
        self.set_sensor()
        self.dimension=dimension
    
    def set_sensor(self, y=0, z=0):
        self.sensor = mgp.Sensor(position=(0,y,z), style_size=1.8)
        self.sensor.position = [ (i,y,z) for i in self.data_x]

    def add_magnets_vector(self, start_x=0, start_r=40, stop_r=40,
                           stop_x=300, number=4,  side='+y', magnets_rotation=0):
        xs = np.linspace(start_x, stop_x, number)
        d = (stop_r-start_r)/(stop_x-start_x)
        for x in xs:
            if side=='+y':
                pos = (start_r+(x-start_x)*d, 0)
                rot = (0, 0, magnets_rotation)
            elif side == '-y': 
                rot = (0, 0, -magnets_rotation)
                pos =( -start_r-(x-start_x)*d, 0)
            elif side == '+z': 
                rot = (0, -magnets_rotation, 0)
                pos=( 0, start_r+(x-start_x)*d)
            elif side == '-z': 
                rot = (0, magnets_rotation, 0)
                pos=( 0, -start_r-(x-start_x)*d)
            cube=mgp.magnet.Cuboid(
                magnetization=(1260, 0, 0),
                dimension=self.dimension,
                position=(x, *pos)
            )
            cube.rotate_from_rotvec(rot )
            self.objects.append(cube)
    
    def add_magnets_cone(self, start_x=0, start_r=40, stop_r=40,
                         stop_x=300, number=4, magnets_rotation=0, sides=['+y','-y','+z','-z']):
        for i in sides:
            self.add_magnets_vector(start_x=start_x, start_r=start_r, stop_r=stop_r,
                stop_x=stop_x, number=number, magnets_rotation=magnets_rotation, side=i
            )

    def show(self):
        mgp.show(self.objects, self.sensor, style_path_show=False)

    def calc(self, show_anim=False, plot=False, extra_plots=[(0,1), (1,0), (0,2), (2,0)], direction=0):
        self.B = self.sensor.getB(self.objects, sumup=True)
        if show_anim:
            self.show()
        if plot:
            self.set_sensor(y=0,z=0)
            plt.clf()
            plt.scatter(self.data_x, self.data_y, label='ref')
            plt.plot(self.data_x,self.B[:,0], label='(0,0)')
            for i in extra_plots:
                y,z=i
                self.set_sensor(y=y, z=z)
                B_local = self.sensor.getB(self.objects, sumup=True)
                plt.plot(self.data_x,B_local[:,0], label=str(i))
            plt.legend()
            plt.grid()
            plt.show()
        return self.B[:,direction]
        

data_x, data_y = np.loadtxt('C:\svnSr\progs\magnet_zs\ZS_computed_values.txt', delimiter='\t', unpack=True)
data_x = data_x*1000
data_y = data_y/100

sides = ['+z','-z',
         '+y','-y'
         ]

def fit_fun(data_x, start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1,
            start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2
            ):
    zs = create_zs(start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1,
            start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2,
            sides = sides
            )
    zs.set_sensor(y=0, z=0)
    return zs.calc()

def create_zs(start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1,
            start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2,
            dimension=(13,25,25), number=4, sides = sides):
    zs = ZeemanSlower(data_x=data_x, data_y=data_y, dimension=dimension)
    zs.add_magnets_cone(start_r=start_r1, stop_r=stop_r1, start_x=start_x1, stop_x=stop_x1,
                        number=number, magnets_rotation=magnets_rotation1,
                        sides = sides )
    zs.add_magnets_cone(start_r=start_r2, stop_r=stop_r2, start_x=start_x2, stop_x=stop_x2,
                        number=number, magnets_rotation=magnets_rotation2,
                        sides = sides)
    return zs

   
p0 = [0, 150, 50, 50, 0,  
      150, 300, 50, 50, 0]
popt, pcov = curve_fit(fit_fun, data_x, data_y, p0=p0)

zs = create_zs(*popt, sides=sides)
#zs = create_zs(*p0, sides=sides)
#zs.set_sensor(y=2, z=2)
#zs.calc(plot=True, show_anim=True, extra_plots=[(0,10), (10,0), (0,20), (20,0)])
#zs.calc(plot=True, show_anim=True, extra_plots=[(0,1), (1,0), (0,2), (2,0), (0,3), (3,0)])
zs.calc(plot=True, show_anim=True, extra_plots=[(0,0), (0,0), (0,2), (2,0)], direction=2)
#print(zs.B)

