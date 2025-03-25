import numpy as np
from gps_simulator import *
from enum import Enum
import matplotlib.cm as cm
from colorist import ColorRGB


from libgps import *
from libnetwork import *



#------------------ Network connexion ---------------------
class Mode(Enum):
    PI=1
    LOCAL_HOST=2

MODE = Mode.LOCAL_HOST
ID = 1
network = AdhocNetwork(id=ID, local_host=(MODE == Mode.LOCAL_HOST))

#----------------------------------------------------------
rainbow_colors = cm.rainbow(np.linspace(0, 1, 20))
rainbow_colors = np.delete(rainbow_colors, 3, axis=1 )
rainbow_colors = 255 * rainbow_colors

LIMIT = 5

TRUE_SIZE = 10
SIZE = TRUE_SIZE *2

points = []
colors = []

def rgb_color(color, text):
    r, g, b = color.astype(int)
    real_color = ColorRGB(r, g, b)

    colored_text = f"{real_color}{text}{real_color.OFF}"
    return colored_text


def create_grid():
    return [[" " for _ in range(SIZE)] for _ in range(SIZE)]

def print_grid(grid):
    print("       " + "   ".join( str(i+1) for i in range(TRUE_SIZE)))
    print("    +" + "----" * TRUE_SIZE + "+")

    for i, row in enumerate(grid):
        i = i+1
        if i%2 != 0 : 
            print("    |" + " ".join(row) + " |") 
        else : 
            print("{: >3d} |".format(int((i+1)/2)) + " ".join(row) + " |") 
    print("    +" + "----" * TRUE_SIZE + "+")

def clear_plot():
    global grid
    for _ in range(SIZE+4):
        print("\033[F", end='')
        print("\033[K", end='')

    grid = create_grid()

# Initialize the grid
grid = create_grid()



# Example: Place an 'O' at (4, 5)

def place_marker(grid, row, col, color, marker="O",):
    grid[row][col] = rgb_color(color, marker)

# Print the grid
print_grid(grid)


def display(fix, lat, lon, altitude):
    global points
    global colors

    if(fix > 0):
        
        clear_plot()

        points.append((lat, lon))
        colors.append(rainbow_colors[int(altitude*2)-1])

        if len(points) > LIMIT : 
            points = list(np.delete(points, 0, axis=0))
            colors = list(np.delete(colors, 0, axis=0))
        
        for i, point in enumerate(points) : 
            lat =  int(point[0]*2)-1
            lon = int(point[1]*2)-1
            color = colors[i]
            if (i == len(points) -1):
                place_marker(grid,  lat, lon, color, "@")
            elif i == len(points) -1 or  i == len(points) -2 :
                place_marker(grid, lat, lon, color, "O")
            elif (i == 0) :
                place_marker(grid, lat, lon, color, ".")
            else :
                place_marker(grid, lat, lon, color, "o")
           

        print_grid(grid)



def adhoc_receiver(network:AdhocNetwork):
    printl("start...")
    while True:
        pos = network.read_data()
        (fix, lat, lon, altitude) = json.loads(pos) # (fix, lat, lon, altitude)
        pos = (fix, lat, lon, altitude)
        print(f"[gps_app.adhoc_receiver] received pos \t : {pos}")
        display(fix, lat, lon, altitude)


adhoc_receiver(network)
