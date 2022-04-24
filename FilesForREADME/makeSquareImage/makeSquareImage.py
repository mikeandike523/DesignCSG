from PIL import Image
import numpy as np
import os

#credit: creating a file picker dialog: https://stackoverflow.com/a/3579783/5166365
from tkinter.filedialog import askopenfilename
filename = askopenfilename()

img = Image.open(filename)

sz = int(input("New size: (-1 for largest dimension): "))
if sz == -1:
    sz = max(img.size[0],img.size[1])

img2 = Image.new(size=(sz,sz),mode="RGB",color=(255,255,255))

padLeft = (sz-img.size[0])//2
padTop = (sz-img.size[1])//2

img2.paste(img,(padLeft,padTop))


dirn = os.path.dirname(filename)
imagen = ".".join(os.path.basename(filename).split(".")[0:-1])
extn = os.path.basename(filename).split(".")[-1]


outfn = os.path.join(dirn,imagen+"_square."+extn).replace("/","\\")


img2.save(outfn)
os.system("%SystemRoot%\\explorer.exe \"{}\"".format(outfn))

