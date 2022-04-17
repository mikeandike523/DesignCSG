import os
os.chdir(os.path.dirname(__file__))

import pymesh
import sys

mesh = pymesh.load_mesh("Exports\\{}".format(sys.argv[1]))
pymesh.save_mesh("Exports\\{}".format(sys.argv[1].replace(".stl",".obj")),mesh)