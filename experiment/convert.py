from itertools import product
import warnings

from numpy import empty, nditer
from xarray import DataArray, Dataset

from . import logger

#: Hack for Py2/3 basestring type compatibility
if 'basestring' not in globals():
    basestring = str


def create_master(exp, var, data=None, new_fields=[]):
    """ Save a dictionary which holds variable data for all
    activation and aerosol case combinations to a dataset
    with those cases as auxiliary indices.

    Parameters:
    -----------
    exp : Experiment
        An Experiment object containing the cases to convert
    var : Var
        A Var object containing the data and cases to infer when
        creating the master dataset.
    data : dict (optional, unless var is a string)
        Dictionary of dictionaries/datasets containing the
        variable data to be collected into a master dataset
    new_fields : list of strs (optional)
        A list of the keys in each DataSet to include in the
        final multi-keyed master

    Returns:
    --------
    master : xarray.DataSet
        A DataSet combining all the sepearate cases into a single
        master, with the case information as auxiliary coordinates.

    """

    if isinstance(var, basestring):
        assert data is not None
        data_dict = data
        new_fields.append(var)
    else:
        # see if it's a Var, and access metadata from the associated
        # Experiment
        if data is None:
            data_dict = var.data
        else:
            data_dict = data
        new_fields.append(var.varname)
        new_fields.extend(var.oldvar)

    all_case_vals = exp.all_case_vals()

    # Post-process the case inspection a bit:
    # 1) Promote any single-value case to a list with one entry
    for i, case_vals in enumerate(all_case_vals):
        if isinstance(case_vals, str):
            all_case_vals[i] = list(case_vals)

    # 2) Make sure they're all still in the data dictionary. This is
    #    circular but a necessary sanity check
    for case_bits in product(*all_case_vals):
        assert case_bits in data_dict

    # Discover the type of the data passed into this method. If
    # it's an xarray type, we'll preserve that. If it's an iris type,
    # then we need to crash for now.
    first_case = next(exp.all_cases())

    proto = data_dict[first_case]
    if isinstance(proto, Dataset):
        return _master_dataset(exp, data_dict, new_fields)
    elif isinstance(proto, DataArray):
        return _master_dataarray(exp, data_dict)
    # elif isinstance(proto, Cube):
    #     raise NotImplementedError("Cube handling not yet implemented")
    else:
        raise ValueError("Data must be an xarray type")


def _master_dataarray(exp, data_dict):
    case_list = [exp._case_data[case] for case in exp.cases]
    stacked_data = _stack_dims(data_dict, case_list, {}, exp)

    test_case = next(exp.all_cases())
    test_da = data_dict[test_case]
    name = test_da.name

    new_coords = test_da.to_dataset().coords
    logger.debug("Creating master dataarray")
    for case in exp.cases:
        logger.debug("   " + case)
        new_coords[case] = exp._case_data[case].vals

    new_dims = list(exp.cases) + list(test_da.dims)

    new_da = DataArray(stacked_data, coords=new_coords,
                       dims=new_dims)
    new_da = copy_attrs(test_da, new_da)
    new_da.name = name

    return new_da


def _stack_dims(data, cases, set_cases, exp):
    """Recursive function to stack multi-dimensional data
    """
    from dask.array import stack as dstack
    from numpy import stack as nstack
    # print(set_cases)
    idx = len(set_cases)
    if idx >= len(cases):
        # print("   leaf")
        tup = exp.case_tuple(**set_cases)
        # print(tup)
        return data[tup].data
    else:
        new_set_cases = set_cases.copy()
        case = cases[idx]

        to_stack = []
        for val in case.vals:
            new_set_cases[case.shortname] = val
            x = _stack_dims(data, cases, new_set_cases, exp)
            to_stack.append(x)

        return dstack(to_stack)

def _master_dataset(exp, data_dict, new_fields):

    all_case_vals = exp.all_case_vals()
    first_case = next(exp.all_cases())
    proto = data_dict[first_case]

    n_case_vals = [len(case_vals) for case_vals in all_case_vals]
    n_cases = len(n_case_vals)

    # Create the new Dataset to populate
    ds_new = Dataset()

    # Add the case coordinates
    for case, longname, vals in exp.itercases():
        ds_new[case] = vals
        ds_new[case].attrs['long_name'] = longname

    logger.debug("Creating master dataset")
    for var in proto.data_vars:
        logger.debug("   "+var)

        # Ensure that all the data has the same dimensions
        bad_keys = []
        data_dict_as_da = {}
        for key, ds in data_dict.items():
            try:
                data_dict_as_da[key] = ds[var]
            except KeyError:
                bad_keys.append(key)
                continue
        if len(data_dict) <= 1:
            raise ValueError("Couldn't coerce data for master array "
                             "concatenation.")
        else:
            ref_da = next(iter(data_dict_as_da.values()))
            for key in bad_keys:
                faux_da = DataArray(empty(ref_da.shape),
                                    dims=ref_da.coords)
                #for case, val in key.items():
                #    faux_da[case] = val
                data_dict_as_da[key] = faux_da
        # data_dict_as_da = exp.apply_to_all(data_dict, lambda x: x[var])
        new_da = _master_dataarray(exp, data_dict_as_da)
        ds_new[var] = new_da

    ds_new = copy_attrs(proto, ds_new)
    return ds_new


def _get_dataset_attr(ds, attr_key):
    if attr_key in ds.attrs:
        return ds.attrs[attr_key]
    else:
        return None


def _get_dataset_names(ds, field):
    """ If possible, return the standard, long, and var names for a
    given selection from an xarray DataSet. """

    dsf = ds[field]

    standard_name, long_name, var_name = None, None, field
    long_name = _get_dataset_attr(dsf, 'long_name')
    standard_name = _get_dataset_attr(dsf, 'standard_name')

    return standard_name, long_name, var_name


def copy_attrs(data_orig, data_new):
    """ Copy the attributes of a DataArray or a DataSet and its
    child DataArrays from one instance to another. If the second
    instance has reduced dimensionality due to some aggregation
    or operation, any truncated coordinates will be ignored.

    """

    if isinstance(data_orig, Dataset):

        # Variables
        for v in data_orig.data_vars:
            field = data_orig[v]
            for attr, val in field.attrs.items():
                data_new[v].attrs[attr] = val

        # Coordinates
        for c in data_orig.coords:
            coord = data_orig.coords[c]
            for attr, val in coord.attrs.items():
                if c in data_new.coords:
                    data_new.coords[c].attrs[attr] = val

        # Metadata
        for attr, val in data_orig.attrs.items():
            data_new.attrs[attr] = val

    elif isinstance(data_orig, DataArray):

        # Variable Metadata
        for att, val in data_orig.attrs.items():
            data_new.attrs[att] = val

        # Coordinates
        for c in data_orig.coords:
            coord = data_orig.coords[c]
            for attr, val in coord.attrs.items():
                if c in data_new.coords:
                    data_new.coords[c].attrs[attr] = val

    else:
        raise ValueError("Couldn't handle type %r" % type(data_orig))

    return data_new
