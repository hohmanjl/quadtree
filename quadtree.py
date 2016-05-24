"""
quadtree.py
Implements a Node and QuadTree class that can be used as
base classes for more sophisticated implementations.
"""
from shapely.geometry import Polygon as shapelyPolygon
from shapely.geometry import Point as shapelyPoint
from shapely.geometry.base import BaseGeometry

__author__ = 'Malcolm Kesson, Miklos Koren, James Hohman'


def bbox_to_coords(bbox):
    if len(bbox) != 4:
        raise TypeError('bbox must have 4 coordinates.')

    x0, y0, x1, y1 = bbox

    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def point_in_rectangle(point, rectangle):
    if type(point) in [tuple, list]:
        x, y = point[0], point[1]
    else:
        x, y = point.x, point.y

    x0, y0, x1, y1 = rectangle

    return x0 <= x <= x1 and y0 <= y <= y1


def get_coords(point):
    if type(point) in [list, tuple]:
        return point[0], point[1]
    else:
        return point.x, point.y


class Feature(object):
    """A wrapper around shapely geometries."""
    def __init__(self, geometry):
        if not isinstance(geometry, BaseGeometry):
            raise Exception

        self.geometry = geometry

    def contains_point(self, point):
        if self.geometry.is_empty:
            return False

        sh_point = shapelyPoint(get_coords(point))

        return (
            point_in_rectangle(point, self.geometry.bounds)
            and self.geometry.intersects(sh_point)
        )

    def contains_rectangle(self, rectangle):
        if self.geometry.is_empty:
            return False

        x0, y0, x1, y1 = rectangle
        points = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        sh_polygon = shapelyPolygon(points)
        return all([point_in_rectangle(point, self.geometry.bounds) for point in
                    points]) and self.geometry.contains(sh_polygon)

    def intersects_rectangle(self, rectangle):
        if self.geometry.is_empty:
            return False

        x0, y0, x1, y1 = rectangle
        points = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        sh_polygon = shapelyPolygon(points)
        return not self.geometry.disjoint(sh_polygon)


class Node(object):
    # In the case of a root node "parent" will be None. The
    # "rect" lists the minx, miny, maxx, maxy of the rectangle
    # represented by the node.
    ROOT = 0
    BRANCH = 1
    LEAF = 2

    def __init__(self, parent, rect, max_points=2):
        self.parent = parent
        self.children = []
        self._points = {}
        self.features = []
        self.number_of_points = 0
        self.max_points = max_points

        self.rectangle = tuple([float(item) for item in rect])
        self.type = Node.LEAF

    @property
    def points(self):
        points = []
        for coordinate, frequency in self._points.items():
            points.extend([coordinate] * frequency)
        return points

    def add_point(self, point):
        # point_feature = featurize(point)
        # point = feature_to_point(point_feature)
        if self.point_coords_in_bbox(point):
            if self.type == Node.LEAF:
                if point in self._points:
                    self._points[point] += 1
                else:
                    self._points[point] = 1
                self.features.append(point)
                self.number_of_points += 1
                if len(self._points) > self.max_points:
                    # the box is crowded, break it up in 4
                    self.subdivide()
            else:
                # find where the point goes
                for child in self.children:
                    if child.point_coords_in_bbox(point):
                        child.add_point(point)
                        self.number_of_points += 1
                        break
        else:
            # point not in box, cannot place
            raise Exception

    def count_overlapping_points(self, feature):
        if feature.contains_rectangle(self.rectangle):
            # all points are within
            return self.number_of_points
        elif feature.intersects_rectangle(self.rectangle):
            if self.type == Node.LEAF:
                # we cannot continue recursion, do a "manual" count
                return sum([
                    frequency for point, frequency in self._points.items()
                    if feature.contains_point(point)
                ])
            else:
                return sum([
                   child.count_overlapping_points(feature)
                   for child in self.children
                ])
        else:
            return 0

    def get_overlapping_points(self, feature):
        if feature.contains_rectangle(self.rectangle):
            # all points are within
            return self.get_all_points()
        elif feature.intersects_rectangle(self.rectangle):
            if self.type == Node.LEAF:
                # we cannot continue recursion, do a "manual" count
                return [
                    point for point in self.features if
                    feature.contains_point(point)
                ]
            else:
                output = []
                for child in self.children:
                    output.extend(child.get_overlapping_points(feature))
                return output
        else:
            return []

    def get_all_points(self):
        if self.type == Node.LEAF:
            return self.features
        else:
            output = []
            for child in self.children:
                output.extend(child.get_all_points())
            return output

    def subdivide(self):
        """
        Recursively subdivides a rectangle. Division occurs
        ONLY if the rectangle spans a "feature of interest".
        :return:
        """
        if not self.type == Node.LEAF:
            # only leafs can be subdivided
            raise Exception

        features = self.features
        self._points = {}
        self.features = []
        self.type = Node.BRANCH

        x0, y0, x1, y1 = self.rectangle
        half_width = (x1 - x0) / 2
        half_height = (y1 - y0) / 2
        rects = [
            (x0, y0, x0 + half_width, y0 + half_height),
            (x0, y0 + half_height, x0 + half_width, y1),
            (x0 + half_width, y0 + half_height, x1, y1),
            (x0 + half_width, y0, x1, y0 + half_height)
        ]
        for rect in rects:
            self.children.append(Node(self, rect, self.max_points))
        for point in features:
            for child in self.children:
                if child.point_coords_in_bbox(point):
                    child.add_point(point)
                    break

    def point_coords_in_bbox(self, point):
        """
        Test if the point's _coordinates_ fall within the
        Node's bounding box.

        NOT whether the Point object exists within the node or not.

        :param point:
        :type point: Point class or tuple of (x, y) coordinates.
        :return: Returns True if the coordinates lie within the
        Node's bounding box.
        :rtype bool:
        """
        x, y = get_coords(point)

        x0, y0, x1, y1 = self.rectangle
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
        else:
            return False

    def walk(self):
        """An iterator over the points of in the Node"""
        if self.type == Node.LEAF:
            for point in self.points:
                yield point
        else:
            for child in self.children:
                for point in child.walk():
                    yield point

    def get_bbox(self):
        return self.rectangle


class Point(object):
    """
    A point object which allows a paylood to be attached.
    """
    def __init__(self, x=None, y=None, data=None):
        self.x = x
        self.y = y
        self.data = data

    def __repr__(self):
        return 'p(%s, %s)' % (str(self.x), str(self.y))

    def __hash__(self):
        if type(self.data) == dict:
            data_hash = hash(frozenset(self.data.items()))
        else:
            data_hash = hash(self.data)

        return hash((self.x, self.y, data_hash))

    def __eq__(self, othr):
        return (self.x, self.y, self.data) == (othr.x, othr.y, othr.data)


class QuadTree(Node):
    def __init__(self, points):
        # pure_points = [feature_to_point(featurize(point)) for point in points]

        # if a split involves 16 checks of containment, the optimal
        # number of points is 16/ln(4)
        super(QuadTree, self).__init__(
            None, rect=self.find_bbox(points), max_points=11
        )
        for point in points:
            self.add_point(point)

    @staticmethod
    def find_bbox(points):
        x, y = get_coords(points[0])
        minx = x
        maxx = x
        miny = y
        maxy = y

        for p in points:
            x, y = get_coords(p)
            if x < minx:
                minx = x
            if x > maxx:
                maxx = x
            if y < miny:
                miny = y
            if y > maxy:
                maxy = y

        return minx, miny, maxx, maxy
