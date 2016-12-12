
import logging
logger = logging.getLogger()

import os
import json
import pkg_resources
import pickle
import warnings

from . io import load_variable

_TAB = "    "

#######################################################################

class VarList(list):
    """ Special type of :class:`list` with some
    better handling for `Var` objects. Based on iris CubeLists
    as a learning example. """

    def __new__(cls, var_list=None):
        """ Create a VarList from a :class:`list` of Vars. """
        vl = list.__new__(cls, var_list)
        if not all( [isinstance(v, Var) for v in vl] ):
            raise ValueError("Some items were not Vars!")
        return vl

    def __str__(self):
        result = [ "%s: %s" % (i, v) for i, v in enumerate(self) ]

        if result:
            result = "\n".join(result)
        else:
            result = "No Vars found."

        return result

class Var(object):
    """ A container object for finding, extracting, modifying, and
    analyzing output from a CESM multi-run experiment.

    A Var allows you to quickly load a minimal set of variables
    necessary for an analysis into memory, and pipeline the
    extraction, analysis, and saving operations.

    Types extending Var add additional features, such as
    applying CDO operators or loading default variables from the
    CESM output which require no pre-processing.

    """
    # TODO: Extend `Mapping` interface so that one doesn't need to use the `data` property to access data
    # TODO: Implement `__enter__` and `__exit__` such that data is loaded and deleted from the `Var` instance
    # TODO: Logging of actions on `Var` instance for writing to new file history after analysis.
    # TODO:Change `oldvar` to automatically populate a 1-element list if not other values passed

    def __init__(self, varname,  oldvar="", long_name="",
                 units="", scale_factor=1., ncap_str="", **kwargs):

        """ Create a container in preparation for an analysis
        pipeline.

        Parameters
        ----------
        varname : str
            A string to use as a convenient, short alias for the
            variable name; this will be the name in the attached
            datasets for any new variable created during the
            extraction process.
        oldvar : str or list of strs, optional
            Either a str or a list of strs of the names of the
            variables which will be used to compose or create
            this new variable.
        long_name : str, optional
            A descriptive, long-form name for this variable.
        units : str, optional
            A udunits-compliant str describing the dimensional
            units of this variable.
        scale_factor : float, optional
            A value to use for re-scaling the output. If no value
            is passed, will default to `1.0`. This is particularly
            useful because it allows lazy conversion to new units.
        ncap_str : str, optional
            A string to be passed to the command line NCO `ncap2`
            for pre-processing during the extraction of the variable
            data
        """

        self.varname = varname
        if not oldvar:
            self.oldvar = varname
        else:
            self.oldvar = oldvar

        self.ncap_str = ncap_str

        # Set any additional arguments as attributes
        self.attributes = kwargs

        # Overwrite any attributes
        self.long_name = long_name
        if long_name:
            self.attributes['long_name'] = long_name

        self.units = units
        if units:
            self.attributes['units'] = units
        else:
            self.attributes['units'] = "1"

        self.scale_factor = scale_factor
        if scale_factor != 1.:
            self.attributes['scale_factor'] = scale_factor

        for attr, val in self.attributes.items():
            self.__dict__[attr] = val

        # Some useful properties to set
        self.name_change = self.varname == self.oldvar

        # Encapsulation of data set when variable is loaded
        self._data = None
        self._cases = None
        self._loaded = False

    def apply(self, func, *args, **kwargs):
        """ Apply a given function to every loaded cube/dataset
        attached to this Var instance. The given function should
        return a new Cube/DataSet instance. """

        if not self._loaded:
            raise Exception("Data is not loaded")
        for key, data in self.data.items():
            self.data[key] = func(data, *args, **kwargs)

    def to_dataarrays(self):
        """ Convert the data loaded using `self.load_datasets()`
        into DataArrays containing only the variable described by
        this. """

        self.apply(lambda ds: ds[self.varname])

    @property
    def cases(self, *keys):
        if not self._loaded:
            raise Exception("Data has not yet been loaded into memory")
        return self._cases
    @cases.deleter
    def cases(self):
        if not self._loaded:
            raise Exception("Data has not yet been loaded into memory")
        self._cases = None
        if self._data is not None:
            self._data = None
        self._loaded = False

    @property
    def data(self):
        if not self._loaded:
            raise Exception("Data has not yet been loaded into memory")
        return self._data
    @data.deleter
    def data(self):
        if not self._loaded:
            raise Exception("Data has not yet been loaded into memory")
        self._data = None
        if self._cases is not None:
            self._cases = None
        self._loaded = False

    @classmethod
    def from_json(cls, json_str):
        jd = json.loads(json_str)
        return Var(**jd)

    def to_json(self):
        """ Return JSON representation of variable info
        as a string. """
        return json.dumps(self.__dict__)

    def __str__(self):

        out = self.varname
        if hasattr(self, "long_name"):
            out += " (%s)" % self.long_name
        if hasattr(self, "units"):
            out += " [%s]" % self.units
        if self._loaded:
            data_type= type(next(iter(self.data.values()))).__name__
            out += "\n[ loaded -> %s(%r)]" % (data_type, self._cases)

        if not (self.oldvar == self.varname):
            olv_str = self.oldvar if isinstance(self.oldvar, str) \
                                  else ",".join(self.oldvar)
            out += "\n" + _TAB + "from fields " + olv_str
        if self.ncap_str:
            out += "\n" + _TAB + "NCAP func: " + self.ncap_str

        return out

    def __repr__(self):
        return self.__str__()

    def _get_atts(self):
        """ Return list of uniquely-identifying attributes. """
        atts = [self.varname, self.units, self.ncap_str]
        if hasattr(self, 'lev_bnds'):
            atts += self.lev_bnds
        if hasattr(self, 'cdo_method'):
            atts += self.cdo_method
        return tuple(atts)

    def __eq__(self, other):
        self_atts, other_atts = self._get_atts(), other._get_atts()
        return self_atts == other_atts

    def __neq__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash( self._get_atts() )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
