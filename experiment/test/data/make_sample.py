#!/usr/bin/env python
"""
This script auto-generates a sample on-disk dataset for testing.

"""

import numpy as np
import os
import pandas as pd
import xarray as xr

from experiment import Experiment, Case

PATH_TO_DATA = os.path.join(os.path.dirname(__file__), "sample")
cases = [
    Case("param1", "Parameter 1", ["a", "b", "c"]),
    Case("param2", "Parameter 2", [1, 2, 3]),
    Case("param3", "Parameter 3", ["alpha", "beta"]),
]
exp = Experiment(
    "sample", cases, timeseries=True, data_dir=PATH_TO_DATA,
    case_path="{param1}_{param2}",
    output_prefix="{param1}.{param2}.{param3}.",
    output_suffix=".tape.nc", validate_data=False
)

VARS = ["temp", "pres", "precip"]


def _make_dataset(varname, seed=None, **var_kws):
    rs = np.random.RandomState(seed)

    _dims = {'time': 10, 'x': 5, 'y': 5}
    _dim_keys = ('time', 'x', 'y')

    ds = xr.Dataset()
    ds['time'] = ('time', pd.date_range('2000-01-01', periods=_dims['time']))
    ds['x'] = np.linspace(0, 10, _dims['x'])
    ds['y'] = np.linspace(0, 10, _dims['y'])
    data = rs.normal(size=tuple(_dims[d] for d in _dim_keys))
    ds[varname] = (_dim_keys, data)

    ds.coords['numbers'] = ('time',
                            np.array(range(_dims['time']), dtype='int64'))

    return ds


if __name__ == "__main__":

    root = exp.data_dir

    for path, case_kws in exp._walk_cases(with_kws=True):
        full_path = os.path.join(root, path)
        os.makedirs(full_path, exist_ok=True)

        prefix = exp.case_prefix(**case_kws)
        suffix = exp.output_suffix

        for v in VARS:
            fn = prefix + v + suffix
            absolute_filename = os.path.join(full_path, fn)

            print(absolute_filename)
            ds = _make_dataset(v)
            ds.to_netcdf(absolute_filename)

    exp.to_yaml(os.path.join(root, "sample.yaml"))
