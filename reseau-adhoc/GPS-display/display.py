import argparse


def display(x, y, z, x_max, y_max, z_max):
    pass

def parse_args():
    global local_port

    parser = argparse.ArgumentParser()
    parser.add_argument('x', type=float)
    parser.add_argument('y', type=float)
    parser.add_argument('z', type=float)

    parser.add_argument('x_max', type=float)
    parser.add_argument('y_max', type=float)
    parser.add_argument('z_max', type=float)

    args = parser.parse_args()
    x = args.x
    y = args.x
    z = args.x

    x_max = args.x
    y_max = args.x
    z_max = args.x

    display(x, y, z, x_max, y_max, z_max)


parse_args()