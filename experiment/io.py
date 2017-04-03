
import xarray as xr

import logging
logger = logging.getLogger()

def load_variable(var_name, path_to_file, squeeze=False,
                  fix_times=True, **extr_kwargs):
    """ Interface for loading an extracted variable into memory, using
    either iris or xarray. If `path_to_file` is instead a raw dataset,
    then the entire contents of the file will be loaded!

    Parameters
    ----------
    var_name : string
        The name of the variable to load
    path_to_file : string
        Location of file containing variable
    squeeze : bool
        Load only the requested field (ignore all others) and
        associated dims
    fix_times : bool
        Correct the timestamps to the middle of the bounds
        in the variable metadata (CESM puts them at the right
        boundary which sucks!)
    extr_kwargs : dict
        Additional keyword arguments to pass to the extractor

    """

    logger.info("Loading %s from %s" % (var_name, path_to_file))

    ds = xr.open_dataset(path_to_file, decode_cf=False, **extr_kwargs)

    # TODO: Revise this logic as part of generalizing time post-processing.
    # Fix time unit, if necessary
    # interval, timestamp = ds.time.units.split(" since ")
    # timestamp = timestamp.split(" ")
    # yr, mm, dy = timestamp[0].split("-")
    #
    # if int(yr) < 1650:
    #     yr = 2001
    # yr = str(yr)
    #
    # # Re-construct at Jan 01, 2001 and re-set
    # timestamp[0] = "-".join([yr, mm, dy])
    # new_units = " ".join([interval, "since"] + timestamp)
    # ds.time.attrs['units'] = new_units

    # TODO: Generalize time post-processing.
    # if fix_times:
    #     assert hasattr(ds, 'time_bnds')
    #     bnds = ds.time_bnds.values
    #     mean_times = np.mean(bnds, axis=1)
    #
    #     ds.time.values = mean_times

    # Be pedantic and check that we don't have a "missing_value" attr
    for field in ds:
        if hasattr(ds[field], 'missing_value'):
            del ds[field].attrs['missing_value']

    # Lazy decode CF
    ds = xr.decode_cf(ds)

    return ds
