import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image

foldername = "E:/image_game"
files = os.listdir(foldername)
files_list = []
for file in files:
    files_list.append(file)

chosen = np.random.choice(files_list)

# img = mpimg.imread(foldername + "/" + chosen)
# imgplot = plt.imshow(img)
# plt.show()
img = Image.open(foldername + "/" + chosen)
img.show()
print(chosen)
