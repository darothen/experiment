from __future__ import absolute_import
from __future__ import print_function


# Set default logging handler to avoid "No handler found" warnings.
# NOTE: Following the pattern at https://github.com/kennethreitz/requests/blob/master/requests/__init__.py
import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
logging.getLogger(__name__).addHandler(NullHandler())

from . experiment import Experiment, Case
from . var import Var, VarList

from . version import  __version__
