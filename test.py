import numpy as np


def color_dist(c1, c2):
    color_diff = (c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2
    return color_diff

test = np.array((((255,255,190),(255,255,191)),((255,255,192),(255,255,193))))

print(np.where(test == (255,255,190)))