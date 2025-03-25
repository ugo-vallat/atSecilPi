import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from gps_simulator import *
from enum import Enum
import matplotlib.cm as cm

from libgps import *
from libnetwork import *


rainbow_colors = cm.rainbow(np.linspace(0, 1, 100))


class Mode(Enum):
    PI=1
    LOCAL_HOST=2

MODE = Mode.LOCAL_HOST
ID = 1
matplotlib.interactive(True)
LIMIT = 3


fig = plt.figure()
subplot = fig.add_subplot(1,1,1)

scatter_plot = subplot.scatter([], [], edgecolor='black')

plt.show()

def display(fix, lat, lon, altitude):
    if(fix > 0):

        offset =  scatter_plot.get_offsets().data
        offset = np.append(offset, [(lat, lon)], axis=0)
        if np.shape(offset)[0] > LIMIT : 
            offset = np.delete(offset, 0, axis=0)

        scatter_plot.set_offsets(offset)

        colors = scatter_plot.get_facecolors()
        colors = np.append(colors, [rainbow_colors[int(altitude*10)]], axis=0)

        while np.shape(colors)[0] > np.shape(offset)[0]:
            colors = np.delete(colors, 0, axis=0)

        scatter_plot.set_facecolor(colors)

        scatter_plot.changed()

network = AdhocNetwork(id=ID, local_host=(MODE == Mode.LOCAL_HOST))

def adhoc_receiver(network:AdhocNetwork):
    printl("start...")
    while True:
        pos = network.read_data()
        (fix, lat, lon, altitude) = json.loads(pos) # (fix, lat, lon, altitude)
        pos = (fix, lat, lon, altitude)
        print(f"[gps_app.adhoc_receiver] received pos \t : {pos}")
        display(fix, lat, lon, altitude)

"""
OK- fix : 0 = pas de données (si on veut simuler l'absence de données, 1 ou 2 = données gps
lat : latitude (coordonnées cartésiennes)
lon = longitude  (coordonnées cartésiennes)
alt = altitude  (coordonnées cartésiennes)
"""
adhoc_receiver(network)
