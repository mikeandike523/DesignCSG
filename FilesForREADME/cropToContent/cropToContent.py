from PIL import Image
import numpy as np
import os

#credit: creating a file picker dialog: https://stackoverflow.com/a/3579783/5166365
from tkinter.filedialog import askopenfilename
filename = askopenfilename()

xmin = float("inf")
xmax = float("-inf")
ymin = float("inf")
ymax = float("-inf")

cropColor = (255,255,255,255) if input("Crop color black (B) or white: ") == "W" else (0,0,0,255)

img = Image.open(filename)

sz1=img.size

for x,y in np.ndindex(img.size):
    data=img.getpixel((x,y))
    if data != cropColor:
        xmin=min(x,xmin)
        ymin=min(y,ymin)
        xmax=max(x,xmax)
        ymax=max(y,ymax)

img=img.crop((xmin,ymin,xmax,ymax))

dirn = os.path.dirname(filename)
basen = os.path.basename(filename)
imagen = ".".join(basen.split(".")[:-1])
extn = basen.split(".")[-1]

sz2=img.size

print(sz1,sz2)

#%SystemRoot%\System32\rundll32.exe "%ProgramFiles%\Windows Photo
#Viewer\PhotoViewer.dll", ImageView_Fullscreen %1

outfn = os.path.join(dirn,imagen+"_cropped."+extn).replace("/","\\")


img.save(outfn)
os.system("%SystemRoot%\\explorer.exe \"{}\"".format(outfn))

