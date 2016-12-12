from itertools import product
import warnings

from numpy import empty, nditer
from xarray import DataArray, Dataset


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

    all_case_vals = exp.all_case_vals()
    first_case = next(exp.all_cases())
    proto = data_dict[first_case]

    n_case_vals = [ len(case_vals) for case_vals in all_case_vals ]
    n_cases = len(n_case_vals)

    new_dims = exp.cases + [str(x) for x in proto.dims]
    new_values = empty(n_case_vals + list(proto.values.shape))
    it = nditer(empty(n_case_vals), flags=['multi_index', ])

    # The logic of this iterator is slightly complicated, but what we're
    # doing is constructing an n-dimensional array where n is the number
    # of cases we're considering. We're looping over the *indices* of that
    # dimension, and performing a lookup in the record of all the case values
    # for all the dimensions (all_case_vals) to create the key which
    # corresponds to this data in the data dictionary which holds the data.
    while not it.finished:
        indx = it.multi_index
        case_indx = tuple([ all_case_vals[n][i] \
                            for i, n in zip(indx, range(n_cases)) ])
        new_values[indx] = data_dict[case_indx].values
        it.iternext()

    # Copy and add the case coordinates
    new_coords = dict(proto.coords)
    for case, vals in zip(exp.cases, all_case_vals):
        new_coords[case] = vals

    da_new = DataArray(new_values, dims=new_dims, coords=new_coords)

    # Copy the attributes for act/aer coords, data itself
    for att, val in proto.attrs.items():
        da_new.attrs[att] = val
    for case, long, _ in exp.itercases():
        da_new.coords[case].attrs['long_name'] = long

    return da_new

def _master_dataset(exp, data_dict, new_fields):

    all_case_vals = exp.all_case_vals()
    first_case = next(exp.all_cases())
    proto = data_dict[first_case]

    n_case_vals = [ len(case_vals) for case_vals in all_case_vals ]
    n_cases = len(n_case_vals)

    # Create the new Dataset to populate
    ds_new = Dataset()

    # Add the case coordinates
    for case, long, vals in exp.itercases():
        ds_new[case] = vals
        ds_new[case].attrs['long_name'] = long

    for f in proto.variables:
        dsf = proto.variables[f]

        # Copy or update the coords/variable data
        if f in proto.coords:
            ds_new.coords[f] = (dsf.dims, dsf.values)
        else:
            if f in new_fields:

                new_dims = exp.cases + [str(x) for x in dsf.dims]
                new_values = empty(n_case_vals + list(dsf.values.shape))

                it = nditer(empty(n_case_vals), flags=['multi_index', ])
                while not it.finished:
                    indx = it.multi_index
                    case_indx = tuple([ all_case_vals[n][i] \
                                      for i, n in zip(indx, range(n_cases)) ])
                    new_values[indx] = data_dict[case_indx].variables[f]
                    it.iternext()

                ds_new[f] = (new_dims, new_values)
            else:
                ds_new[f] = (dsf.dims, dsf.values)

        # Set attributes for the variable
        for att, val in dsf.attrs.items():
            ds_new[f].attrs[att] = val

    # Set global attributes
    for att, val in proto.attrs.items():
        ds_new.attrs[att] = val

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
