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

maxWidth = max(sz1[0],sz2[0])
maxHeight = max(sz1[1],sz2[1])

padW1 = maxWidth - sz1[0]
padH1 = maxHeight - sz1[1]

padW2 = maxWidth - sz2[0]
padH2 = maxHeight -sz2[1]

padW1Left = padW1//2; padW1Right = padW1-padW1//2
padH1Left = padH1//2; padH1Right = padH1-padH1//2
padW2Left = padW2//2; padW2Right = padW2-padW2//2
padH2Left = padH2//2; padH2Right = padH2-padH2//2

newimg1 = Image.new(size=(maxWidth,maxHeight),color = background,mode="RGB")
newimg2 = Image.new(size=(maxWidth,maxHeight),color = background,mode="RGB")

newimg1.paste(img1,(padW1Left,padW1Right))
newimg2.paste(img2,(padW2Left,padW2Right))



dirn1 = os.path.dirname(filepath1)
dirn2 = os.path.dirname(filepath2)
ext1 = os.path.basename(filepath1).split(".")[-1]
ext2 = os.path.basename(filepath1).split(".")[-1]
n1 = ".".join(os.path.basename(filepath1).split(".")[0:-1])
n2 = ".".join(os.path.basename(filepath2).split(".")[0:-1])

newimg1.save(os.path.join(dirn1,n1+"_padded"+"."+ext1))
newimg2.save(os.path.join(dirn2,n2+"_padded"+"."+ext2))

print(n1,n2)
