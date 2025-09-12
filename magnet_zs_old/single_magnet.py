import magpylib as magpy
import matplotlib.pyplot as plt
source = magpy.magnet.Cuboid(
    magnetization=(1100,0,0),
    dimension=(13,25,25),
    position=(0,0,0)
)

def calc(xdata):
    out = []
    for x in xdata:
        out.append(source.getB((x,0,0))[0])
    return out

xdata = [15, 19, 19.5, 29, 35, 44, 68]
ymes = [185, 112, 110, 45, 28, 15, 5]
y=calc(xdata)
plt.plot(xdata,y)
plt.scatter(xdata, ymes)
plt.show()

#magpy.show(source)

#observer = (0,0,20)
#B = source.getB(observer)
#print(B)