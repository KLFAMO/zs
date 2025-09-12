import magpylib as mgp
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


class Magnet:
    def __init__(self, name='magnet', size=(13,25,25), position=(0,0,0), rotation=(0,0,0)):
        self.name = name
        self.position = position
        self.size = size
        self.rotation = rotation

    # def fc_draw(self, gap_size=1, z_extend = 6):
    #     App.ActiveDocument.addObject("Part::Box","Box")
    #     ob = App.ActiveDocument.ActiveObject
    #     ob.Label = self.name
    #     ob.Length = self.size[0] + gap_size
    #     ob.Width = self.size[1] + gap_size
    #     ob.Height = self.size[2] + gap_size + z_extend
    #     ob.Placement = App.Placement(
    #         App.Vector(*(-(self.size[i]+gap_size)/2. for i in [0,1,2])),
    #         App.Rotation(App.Vector(0,0.0,0),0)
    #     )
    #     print(self.rotation)
    #     Draft.rotate([ob], self.rotation[2], App.Vector(0,0,0), axis=App.Vector(0,0,1), copy=False)
    #     Draft.rotate([ob], self.rotation[1], App.Vector(0,0,0), axis=App.Vector(0,1,0), copy=False)
    #     Draft.move([ob], App.Vector(*self.position))
    #     Draft.move([ob], App.Vector(0,0,-z_extend))
    #     App.ActiveDocument.recompute()
    

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
        if not data_x:
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
            rad2deg = 360/(2*np.pi)
            cube.rotate_from_rotvec(rot)
            self.mgp_objects.append(cube)
            self.magnets.append(Magnet(position=(x, *pos), rotation=tuple([x*rad2deg for x in rot])))
    
    def add_magnets_cone(self, start_x=0, start_r=40, stop_r=40,
                         stop_x=300, number=4, magnets_rotation=0, mrg=0,
                        sides=['+y','-y','+z','-z']):
        for i in sides:
            self.add_magnets_vector(start_x=start_x, start_r=start_r, stop_r=stop_r,
                stop_x=stop_x, number=number, magnets_rotation=magnets_rotation, mrg=mrg, side=i
            )

    def show(self):
        mgp.show(self.mgp_objects, self.sensor, style_path_show=False)

    def calc(self, show_anim=False, plot=False, extra_plots=[(0,1), (1,0), (0,2), (2,0)],
            direction=0, data_x=None):
        self.B = self.sensor.getB(self.mgp_objects, sumup=True)
        if show_anim:
            self.show()
        if plot:
            if data_x:
                self.set_sensor(y=0, z=0, data_x=data_x)
                self.B = self.sensor.getB(self.mgp_objects, sumup=True)
                plt.clf()
                plt.scatter(self.data_x, self.data_y, label='ref')
                plt.plot(data_x,self.B[:,0], label='(0,0)')
            else:
                self.set_sensor(y=0,z=0)
                plt.clf()
                plt.scatter(self.data_x, self.data_y, label='ref')
                plt.plot(self.data_x,self.B[:,0], label='(0,0)')
            for i in extra_plots:
                y,z=i
                self.set_sensor(y=y, z=z)
                B_local = self.sensor.getB(self.mgp_objects, sumup=True)
                plt.plot(self.data_x,B_local[:,0], label=str(i))
            plt.legend()
            plt.grid()
            plt.show()
        return self.B[:,direction]
        

data_x, data_y = np.loadtxt('C:\svnSr\progs\magnet_zs\ZS_computed_values.txt', delimiter='\t', unpack=True)
data_x = data_x*1000
data_y = data_y/100

sides = [#'+z','-z',
         '+y','-y'
         ]

def fit_fun(data_x, start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1, mrg1,
            start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2, mrg2
            ):
    zs = create_zs(start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1, mrg1,
            start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2, mrg2,
            sides = sides
            )
    zs.set_sensor(y=0, z=0)
    return zs.calc()

def create_zs(start_x1, stop_x1, start_r1, stop_r1, magnets_rotation1, mrg1,
            start_x2, stop_x2, start_r2, stop_r2, magnets_rotation2, mrg2,
            dimension=(13,25,25), number=4, sides = sides):
    zs = ZeemanSlower(data_x=data_x, data_y=data_y, dimension=dimension)
    zs.add_magnets_cone(start_r=start_r1, stop_r=stop_r1, start_x=start_x1, stop_x=stop_x1,
                        number=number, magnets_rotation=magnets_rotation1, mrg=mrg1,
                        sides = sides )
    zs.add_magnets_cone(start_r=start_r2, stop_r=stop_r2, start_x=start_x2, stop_x=stop_x2,
                        number=number, magnets_rotation=magnets_rotation2, mrg=mrg1,
                        sides = sides)
    return zs


p0 = [0, 140, 50, 50, 0, 0,  
      160, 300, 50, 50, 0, 0]

min_r=20
min = [0, 50, min_r, min_r, -400, -100,
       50, 100, min_r, min_r, -400, -100]

max_r=55 #59
max = [100, 250, max_r, max_r, 400, 100,
       250, 316, max_r, max_r, 400, 100]
bounds = (min, max)

popt, pcov = curve_fit(fit_fun, data_x, data_y, p0=p0, bounds=bounds)

zs = create_zs(*popt, sides=sides)
zs.set_sensor(y=0, z=0)
#zs.calc(plot=True, show_anim=True, extra_plots=[(0,10), (10,0), (0,20), (20,0)])
#zs.calc(plot=True, show_anim=True, extra_plots=[(0,1), (1,0), (0,2), (2,0), (0,3), (3,0)])
data_x = list(range(500, -150, -2))
zs.calc(plot=True, show_anim=True, extra_plots=[], direction=0, data_x=data_x)
print([x.position[0] for x in zs.magnets])
#print(zs.B)

# for i in zs.magnets:
#     i.fc_draw()
