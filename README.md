# quadtree

My fork of [Miklós Koren](https://github.com/korenmiklos)'s
[quadtree](https://github.com/ceumicrodata/quadtree)
implementation in Python.

Which is based off of Malcolm Kesson's
[quadtree](http://www.fundza.com/algorithmic/quadtree/index.html) code.

---

A quadtree implementation in Python to count many points within
complex geometric shapes.


# Installation
1. Install Shapely
   1. Install `libgeos` dependency.

      ```
      $ sudo apt-get install libgeos-c1
      ```
   2. Install shapely.

      ```
      $ pip install Shapely
      ```

# Example
```
import quadtree
from shapely.geometry import Polygon

qt = quadtree.QuadTree([(0, 0), (0, 1), (5, 1)])

# Test if the points exist in the bounding box established by the points above.
assert qt.contains_point((0, 0))
assert qt.contains_point((0.1, 0.1))
assert not qt.contains_point((-0.1, 0.1))

# Walk all the points in the quadtree
for point in qt.walk():
    print point

> (0, 1)
> (5, 1)
> (0, 0)

# Find points that exist within the bouding box below.
rect = Polygon([(4, 0), (6, 0), (6, 1), (4, 1)])
print qt.get_overlapping_points(quadtree.Feature(rect))

> []

rect = Polygon([(0, 0), (6, 0), (6, 2), (4, 2)])
print qt.get_overlapping_points(quadtree.Feature(rect))

# Current implementation returns all points as fake geometry objects.
> [{'geometry': {'type': 'Point', 'coordinates': [5, 1]},
'type': 'Feature', 'properties': {'name': 'Dinagat Islands'}}]
```