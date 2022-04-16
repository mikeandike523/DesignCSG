import pptk
import numpy as np
with open("box_points.txt") as fl:
    items = []
    for line in fl:
        items.append(list(map(float,line.split(" "))))

pptk.viewer(np.array(items))