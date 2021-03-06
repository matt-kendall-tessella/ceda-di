"""
Module for holding and exporting file metadata as JSON documents.
"""

from __future__ import division
import hashlib
import json
import logging
import math
from pyhull.convex_hull import qconvex


class Properties(object):
    """
    A class to hold, manipulate, and export geospatial metadata at file level.
    """
    def __init__(self, filesystem=None, spatial=None,
                 temporal=None, data_format=None, parameters=None,
                 **kwargs):
        """
        Construct a 'ceda_di.metadata.Properties' ready to export as JSON or dict
        (see "doc/schema.json")

        :param dict filesystem: Filesystem information about file
        :param dict spatial: Spatial information about file
        :param dict temporal: Temporal information about file
        :param dict data_format: Data format information about file
        :param list parameters: Parameter objects in list
        :param **kwargs: Key-value pairs of any extra relevant metadata.
        """

        self.logger = logging.getLogger(__name__)

        self.filesystem = filesystem
        self.temporal = temporal
        self.data_format = data_format

        if parameters is not None:
            self.parameters = [p.get() for p in parameters]
        else:
            self.parameters = None

        self.spatial = spatial
        if self.spatial is not None:
            self.spatial["lat"] = filter(self.valid_lat, self.spatial["lat"])
            self.spatial["lon"] = filter(self.valid_lon, self.spatial["lon"])
            self.spatial = self._to_geojson(self.spatial)

        self.misc = kwargs
        self.properties = {
            "_id": hashlib.sha1(self.filesystem["path"]).hexdigest(),
            "data_format": self.data_format,
            "file": self.filesystem,
            "misc": self.misc,
            "parameters": self.parameters,
            "spatial": self.spatial,
            "temporal": self.temporal,
        }

    @staticmethod
    def valid_lat(num):
        """
        Return true if 'num' is a valid latitude.
        :param float num: Number to test
        :return: True if 'num' is valid, else False
        """
        if num < -90 or num > 90:
            return False
        return True

    @staticmethod
    def valid_lon(num):
        """
        Return true if 'num' is a valid longitude.
        :param float num: Number to test
        :return: True if 'num' is valid, else False
        """
        if num < -180 or num > 180:
            return False
        return True

    def _gen_bbox(self, coord_list):
        """
        Generate and return a bounding box for the given geospatial data.
        :param dict coord_list: Dictionary with "lat" and "lon" lists
        :return dict bbox: A bounding-box formatted in the GeoJSON style
        """
        lons = coord_list["lon"]
        lats = coord_list["lat"]

        lon_lo, lon_hi = self._get_min_max(lons, filter_func=self.valid_lon)
        lat_lo, lat_hi = self._get_min_max(lats, filter_func=self.valid_lat)

        bbox = {
            "type": "MultiPoint",
            "coordinates": [[lon_lo, lat_lo],
                            [lon_lo, lat_hi],
                            [lon_hi, lat_hi],
                            [lon_hi, lat_lo]]
        }

        return bbox

    def _gen_hull(self, coord_list):
        """
        Generate and return a convex hull for the given geospatial data.
        :param list coord_list: Normalised and uniquified set of coordinates
        :return dict chul: A convex hull formatted in the GeoJSON style
        """

        chull = {
            "type": "Polygon"
        }

        qhull_output = qconvex('p', coord_list)
        hull_coords = []
        for point in qhull_output[2:]:
            coords = point.split(" ")
            try:
                hull_coords.append((float(coords[0]), float(coords[1])))
            except ValueError as val:
                self.logger.error("Cannot convert to float: (%s) [%s]",
                                  val, str(coords))

        chull["coordinates"] = hull_coords
        return chull

    def _gen_coord_summary(self, coord_list):
        """
        Pull 30 evenly-spaced coordinates from a given list
        :param list coord_list: Normalised and unique set of coordinates
        :return dict summ: A summary formatted in the GeoJSON style
        """

        num_points = 30
        summ = {
            "type": "LineString"
        }

        lons = coord_list["lon"]
        lats = coord_list["lat"]

        step = int(math.ceil(len(lons) / num_points))
        lons = lons[::step]
        lats = lats[::step]

        summ["coordinates"] = zip(lons, lats)

        return summ

    @staticmethod
    def _get_min_max(item_list, filter_func=None):
        """
        Return a tuple containing the (highest, lowest) values in the list.
        :param list item_list: List of comparable data items
        :param function filter_func: Function that returns True for good values
        :return tuple: Tuple of (highest, lowest values in the list)
        """
        if len(item_list) < 1:
            return (None, None)

        # Filter out ignore_value (useful for _FillValue, etc)
        if filter_func is not None:
            item_list = [i for i in item_list if filter_func(i)]

        high = max(item_list)
        low = min(item_list)

        return (low, high)

    @staticmethod
    def _to_wkt(spatial):
        """
        Convert lats and lons to a WKT linestring.

        :param dict spatial: A dict with keys 'lat' and 'lon' (as lists)
        :return: A Python string representing a WKT linestring
        """
        lats = spatial["lat"]
        lons = spatial["lon"]

        coord_list = set()
        for lat, lon in zip(lats, lons):
            coord_list.add("%f %f" % (lat, lon))

        sep = ", "
        coord_string = sep.join(coord_list)
        linestring = "LINESTRING (%s)" % coord_string

        return linestring

    def _to_geojson(self, spatial):
        """
        Convert lats and lons to a GeoJSON-compatible type.

        :param dict spatial: A dict with keys 'lat' and 'lon' (as lists)
        :return: A Python dict representing a GeoJSON-compatible coord array
        """
        lats = spatial["lat"]
        lons = spatial["lon"]

        if len(lats) > 0 and len(lons) > 0:
            geojson = {
                "geometries": {
                    "bbox": self._gen_bbox(spatial),
                    "summary" : self._gen_coord_summary(spatial)
                }
            }

            return geojson
        return None

    def __str__(self):
        """
        Format file properties to JSON when coercing object to string.

        :return: A Python string containing JSON representation of object.
        """
        return json.dumps(self.properties, default=repr)

    def as_json(self):
        """
        Return metadata as JSON string.

        :return str: JSON document describing metadata.
        """
        return self.__str__()

    def as_dict(self):
        """
        Return metadata as dict object.

        :return dict: Dictionary describing metadata
        """
        return self.properties


class Parameter(object):
    """
    Placeholder/wrapper class for metadata parameters
    :param str name: Name of variable/parameter
    :param dict other_params: Optional - Dict containing other param metadata
    """
    def __init__(self, name, other_params=None):
        self.items = []
        self.name = name

        # Other arbitrary arguments
        if other_params:
            for key, value in other_params.iteritems():
                self.items.append(
                    self.make_param_item(key.strip(), unicode(value).strip()))

    @staticmethod
    def make_param_item(name, value):
        """
        Convert a name/value pair to dictionary (for better indexing in ES)
        :param str name: Name of the parameter item (e.g. "long_name_fr", etc)
        :param str value: Value of the parameter item (e.g. "Radiance")
        :return dict: Dict containing name:value information
        """
        return {"name": name,
                "value": value}

    def get(self):
        """Return the list of parameter items"""
        return self.items
