import numpy as np
import matplotlib.pyplot as plt
import random
def min_distance(points, r):
    n = len(points)
    for i in range(n):
        for j in range(i+1,n):
            d = np.linalg.norm(points[i]-points[j])
            if d < r:
                return False
    return True

def estimate_probability(n,r,trials = 10000):
    count = 0
    for _ in range(trials):
        points = np.random.rand(n,2)
        if min_distance(points,r):
            count+=1

    return count/trials

trials = 200
n_values = np.arange(2,50)
r_values = np.linspace(0.01,0.2,20)
X,Y = np.meshgrid(n_values,r_values)
Z = np.zeros_like(X, dtype=float)
for i in range(X.shape[0]):
    for j in range(X.shape[1]):

        n = int(X[i,j])
        r = Y[i,j]

        Z[i,j] = estimate_probability(n, r, trials)
Z_theory = np.exp(-0.5*np.pi*X*(X-1)*Y**2)
fig = plt.figure()
ax = fig.add_subplot(111,projection = '3d')
ax.plot_surface(X,Y,Z)
ax.plot_surface(X,Y,Z_theory)
ax.set_xlabel("number of points")
ax.set_ylabel("minimum gap between points")
ax.set_zlabel("estimated probability")
plt.show()

