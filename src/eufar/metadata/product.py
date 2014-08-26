"""
Module for holding and exporting file metadata as JSON documents.
"""

from __future__ import division
import json
import logging
from pyhull.convex_hull import qconvex


class Properties(object):
    """
    A class to hold, manipulate, and export geospatial metadata at file level.
    """
    def __init__(self, file_level=None, spatial=None,
                 temporal=None, data_format=None, parameters=None,
                 **kwargs):
        """
        Construct a 'eufar.metadata.Properties' ready to export as JSON or dict
        (see "doc/schema.json")

        :param dict file_level: File-level information about file
        :param dict spatial: Spatial information about file
        :param dict temporal: Temporal information about file
        :param dict data_format: Data format information about file
        :param list parameters: Parameter objects in list
        :param **kwargs: Key-value pairs of any extra relevant metadata.
        """

        self.logger = logging.getLogger()

        self.file_level = file_level
        self.temporal = temporal
        self.data_format = data_format

        if parameters is not None:
            self.parameters = [p.__dict__ for p in parameters]
        else:
            self.parameters = None

        self.spatial = spatial
        if self.spatial is not None:
            self.spatial = self._to_geojson(self.spatial)

        self.misc = kwargs
        self.properties = {
            "data_format": self.data_format,
            "file": self.file_level,
            "misc": self.misc,
            "parameters": self.parameters,
            "spatial": self.spatial,
            "temporal": self.temporal,
        }

    def _gen_bbox(self, spatial):
        """
        Generate and return a bounding box for the given geospatial data.
        :param dict spatial: Dictionary with "lat" and "lon" keys w/coordinates
        :return dict bbox: A bounding-box formatted in the GeoJSON style
        """
        lons = spatial["lon"]
        lats = spatial["lat"]

        lon_lo, lon_hi = self._get_min_max(lons)
        lat_lo, lat_hi = self._get_min_max(lats)

        bbox = {
            "type": "MultiPoint",
            "coordinates": [[lon_lo, lat_lo],
                            [lon_lo, lat_hi],
                            [lon_hi, lat_lo],
                            [lon_hi, lat_hi]]
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

    @staticmethod
    def _get_min_max(item_list):
        """
        Return a tuple containing the (highest, lowest) values in the list.
        :param list item_list: List of comparable data items
        :return tuple: Tuple of (highest, lowest values in the list)
        """
        if len(item_list) < 1:
            return (None, None)

        high = max(item_list)
        low = min(item_list)

        return (high, low)

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
            geojson = {}
            coord_set = set()
            for lat, lon in zip(lats, lons):
                coord_set.add((lon, lat))

            coord_list = list(coord_set)
            geojson["geometries"] = {
                "coordinates": coord_list,
            }

            if len(coord_list) > 3:
                geojson["geometries"]["hull"] = self._gen_hull(coord_list)
                geojson["geometries"]["bbox"] = self._gen_bbox(spatial)

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
        self.name = name

        # Other arbitrary arguments
        if other_params:
            for k, v in other_params.iteritems():
                setattr(self, k, v)
