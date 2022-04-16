#import pptk
import numpy as np
from itertools import combinations
with open("box_points.txt") as fl:
    points= []
    for line in fl:
        points.append(list(map(float,line.split(" "))))

#pptk.viewer(np.array(items))

'''
import pyvista as pv

points=np.array(points)
cloud = pv.PolyData(points)
volume = cloud.delaunay_3d(alpha=0.01)
shell = volume.extract_geometry()
shell.plot()
'''

'''
from scipy.spatial import Delaunay
tri = Delaunay(points)

print(tri.simplices)

import struct




with open("Untitled.stl","wb") as fl:
    for _ in range(80):
        fl.write(struct.pack("<x"))
    fl.write(struct.pack("<I",len(tri.simplices)*4))
    for simplex in tri.simplices:
        for indices in combinations(simplex, 3):
            pts = points[indices,:]
            fl.write(struct.pack("<fff",0.0,0.0,0.0))
            for pt in pts:
                fl.write(struct.pack("<fff",*pt))
            fl.write(struct.pack("<H",0))

import os
os.system("start untitled.stl")
'''

import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt

#https://stackoverflow.com/questions/62948421/how-to-create-point-cloud-file-ply-from-vertices-stored-as-numpy-array
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(points)
pcd.estimate_normals()

with open("horse_with_normals.xyz","w") as fl:
    for point,normal in zip(pcd.points, pcd.normals):
        fl.write(("{:f} "*5+"{:f}\n").format(*point,*normal))

 #credit https://github.com/mmolero/pypoisson

from pypoisson import poisson_reconstruction
from ply_from_array import points_normals_from, ply_from_array

filename = "horse_with_normals.xyz"
output_file = "horse_reconstruction.ply"

#Helper Function to read the xyz-normals point cloud file
points, normals = points_normals_from(filename)

faces, vertices = poisson_reconstruction(points, normals, depth=10)

#Helper function to save mesh to PLY Format
ply_from_array(vertices, faces, output_file=output_file)

import os
os.system("start horse_reconstruction.ply")