from stl import mesh
import numpy as np
from scipy.spatial import KDTree
import pickle
from collections import deque
import random

try:
    with open("vars.pk","rb") as fl:
        unique_pts,unique_triangles = pickle.load(fl) 
except:

    FUSION_RADIUS = 0.005
    NUM_NN = 10

    untitled = mesh.Mesh.from_file('Untitled.stl')

    pts = []
    pts_idx = list(zip(pts,range(len(pts))))

    for triangle in zip(untitled.v0,untitled.v1,untitled.v2):
        pts.append(triangle[0])
        pts.append(triangle[1])
        pts.append(triangle[2])

    tree = KDTree(pts)
    indices = list(range(len(pts)))

    for I in range(len(pts)):
        pt = pts[I]
        d,nbr_idxs = tree.query(pt,NUM_NN)
        for J,nbr_idx in enumerate(nbr_idxs):
            nbr = pts[nbr_idx]
            if d[J] < FUSION_RADIUS:
                indices[nbr_idx] = indices[I]

    unique = list(set(indices))
    unique_pts = np.zeros((len(unique),3),dtype=float)

    unique_triangles = []

    for I,idx in zip(range(len(indices)),indices):
        pt = pts[I]
        J = unique.index(idx)
        unique_pts[J,:] = pt

    for triangle_idx in range(len(untitled.v0)):
        A =triangle_idx *3 +0
        B =triangle_idx *3 +1
        C =triangle_idx *3 +2
        unique_triangles.append([unique.index(indices[A]),unique.index(indices[B]),unique.index(indices[C])])

    fl= open("vars.pk","wb")
    pickle.dump((unique_pts,unique_triangles),fl)
    fl.close()



print(unique_pts)
print(unique_triangles)


#test that points were fused correctly

import struct

dump = open("dump.stl","wb")

for _ in range(80):
    dump.write(struct.pack("x"))

dump.write(struct.pack("I",len(unique_triangles)))

for triangle in unique_triangles:
    dump.write(struct.pack("fff",0.0,0.0,0.0))
    print(triangle)
    A,B,C = triangle
    Av,Bv,Cv = unique_pts[A],unique_pts[B],unique_pts[C]
    dump.write(struct.pack("fff",Av[0],Av[1],Av[2]))
    dump.write(struct.pack("fff",Bv[0],Bv[1],Bv[2]))
    dump.write(struct.pack("fff",Cv[0],Cv[1],Cv[2]))
    dump.write(struct.pack("H",0))

dump.close()



'''
use_count = np.zeros(len(unique_pts))
connections = []
for _ in range(len(use_count)):
    connections.append([])

for tidx,triangle in enumerate(unique_triangles):
    print(triangle)
    A,B,C = triangle
    use_count[A]  = use_count[A]+1
    use_count[B]  = use_count[B]+1
    use_count[C]  = use_count[C]+1
    connections[A].extend([B,C])
    connections[B].extend([A,C])
    connections[C].extend([A,B])
     
bad_points = []
points_bad = np.zeros((len(unique_pts),),dtype =bool)
for I,use  in enumerate(use_count):
    if use < 3:
        bad_points.append(I)
        points_bad[I] = True

print(connections)

def find_loop(bad_ptidx):
    stack = []
    stack.append((bad_ptidx,[bad_ptidx]))
    while len(stack) > 0:
        idx,path_so_far = stack.pop()
        conns = connections[idx]
        for conn in conns:
            if points_bad[conn]:
                if conn == bad_ptidx:
                    return path_so_far
                stack.append((conn,path_so_far+[conn]))
    return None


for test_idx in bad_points:
    bad_count=0
    for conn in connections[test_idx]:
        if points_bad[conn]:
            bad_count+=1
    #print(bad_count)
    if bad_count > 2:
        print(find_loop(test_idx))

import pptk
v=pptk.viewer(unique_pts[bad_points])
'''

def rev_edge(ed):
    return (ed[1],ed[0])

edges= []

for tidx,triangle in enumerate(unique_triangles):
    A,B,C = triangle
    edges.append((A,B))
    edges.append((B,C))
    edges.append((C,A))


connections = []
for _ in range(len(unique_pts)):
    connections.append([])

for tidx,triangle in enumerate(unique_triangles):
    print(triangle)
    A,B,C = triangle
    connections[A].extend([B,C])
    connections[B].extend([A,C])
    connections[C].extend([A,B])

freqs = {}

for edge in edges:
    if edge in freqs:
        freqs[edge] += 1
    else:
        if rev_edge(edge) in freqs:
            freqs[rev_edge(edge)] += 1
        else:
            freqs[edge] = 1

bad_points = set()

for freq in freqs:
    if freqs[freq] < 2:
        A=freq[0]
        B=freq[1]
        bad_points.add(A)
        bad_points.add(B)

 
points_bad = np.zeros((len(unique_pts),),dtype =bool)
for I in range(len(points_bad)):
    if I in bad_points:
        points_bad[I] = True

startpoints = np.zeros((len(unique_pts),),dtype=bool)

def find_loop(bad_ptidx):
    stack = []
    stack.append((connections[bad_ptidx][0],[bad_ptidx]))
    marked = np.zeros((len(connections),),dtype=bool)
    marked[bad_ptidx] = True
    while len(stack) > 0:
        idx,path_so_far = stack.pop()

        marked[idx] = True
        conns = connections[idx]
        for conn in conns:
            if points_bad[conn]:
                if conn == bad_ptidx and idx!=connections[bad_ptidx][0]:
                    return path_so_far + [conn]
                if not marked[conn]:
                    stack.append((conn,path_so_far+[conn]))
    return None

loops = set()


for test_idx in bad_points:
    if startpoints[test_idx]: continue
    lp=find_loop(test_idx)
    if lp is not None:
        if len(lp) >=3:
            for item in lp:
                startpoints[item] = True
            loops.add(tuple(lp))


import pptk
v=pptk.viewer(unique_pts[list(random.choice(list(loops)))])









