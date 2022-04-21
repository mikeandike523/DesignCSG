from PIL import Image
import numpy as np
import os

#credit: creating a file picker dialog: https://stackoverflow.com/a/3579783/5166365
from tkinter.filedialog import askopenfilename
filepath1 = askopenfilename()
filepath2 = askopenfilename()

background = (255,255,255)


img1 = Image.open(filepath1)
img2 = Image.open(filepath2)

sz1 = img1.size
sz2 = img2.size

minWidth = max(sz1[0],sz2[0])
minHeight = max(sz1[1],sz2[1])

cropStartW1 = (sz1[0]-minWidth)//2
cropStartH1 = (sz1[1]-minHeight)//2
cropStartW2 = (sz2[0]-minWidth)//2
cropStartH2 = (sz2[1]-minHeight)//2





newimg1 = img1.crop((cropStartW1,cropStartH1,cropStartW1+minWidth,cropStartH1+minHeight))
newimg2 = img2.crop((cropStartW2,cropStartH2,cropStartW2+minWidth,cropStartH2+minHeight))


dirn1 = os.path.dirname(filepath1)
dirn2 = os.path.dirname(filepath2)
ext1 = os.path.basename(filepath1).split(".")[-1]
ext2 = os.path.basename(filepath1).split(".")[-1]
n1 = ".".join(os.path.basename(filepath1).split(".")[0:-1])
n2 = ".".join(os.path.basename(filepath2).split(".")[0:-1])

newimg1.save(os.path.join(dirn1,n1+"_cropped"+"."+ext1))
newimg2.save(os.path.join(dirn2,n2+"_cropped"+"."+ext2))

print(n1,n2)
