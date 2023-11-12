import cv2
import numpy as np

GRID_W = 10
WIDTH = 2000
HEIGHT = 1000

img = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8) * 255

# create checker
for i in range(0, HEIGHT, GRID_W):
    for j in range(0, WIDTH, GRID_W):
        if (i // GRID_W + j // GRID_W) % 2 == 0:
            img[i:i + GRID_W, j:j + GRID_W] = 220

cv2.imwrite('./imgs/background.png', img)
