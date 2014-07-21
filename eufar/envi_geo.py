from io import envi
from _dataset import _geospatial


class ENVI(_geospatial):
    def __init__(self):
        raise NotImplementedError("Do not instantiate this class. Use BIL/BSQ.")
        
    def get_geospatial(self):
        """
        :param str header_fpath: Filename of header file
        :return dict: A dict containing geospatial and temporal information
        """
        
        data = self.b.read()
        swath_path = {
            "lines": self.b.hdr["lines"],
            "time": data[0],
            "lat": data[1],
            "lon": data[2],
            "alt": data[3],
            "roll": data[4],
            "pitch": data[5],
            "heading": data[6]
        }

        return swath_path

class BIL(ENVI):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.header_path = header_path
        self.path = path
        self.unpack_fmt = unpack_fmt

    def __enter__(self):
        """
        Used to set up file when used in context manager.
        :return self:
        """
        self.b = envi.BilFile(self.header_path,
                              self.path,
                              self.unpack_fmt)
        return self

    def __exit__(self, *args):
        pass
        

class BSQ(ENVI):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.header_path = header_path
        self.path = path
        self.unpack_fmt = unpack_fmt

    def __enter__(self):
        """
        Used to set up file as context manager.
        :return self:
        """
        self.b = envi.BsqFile(self.header_path,
                              self.path,
                              self.unpack_fmt)
        return self

    def __exit__(self):
        pass
