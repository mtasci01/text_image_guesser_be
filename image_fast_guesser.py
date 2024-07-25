import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

foldername = "C:/Users/XYZ/Downloads/guided_tours/guided_tours"
files = os.listdir(foldername)
files_list = []
for file in files:
    files_list.append(file)

chosen = np.random.choice(files_list)

img = mpimg.imread(foldername + "/" + chosen)
imgplot = plt.imshow(img)
plt.show()
print(chosen)
