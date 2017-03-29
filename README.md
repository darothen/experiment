# experiment: Managing modeling experiment output

[![Build Status](https://travis-ci.org/darothen/experiment.svg?branch=master)](https://travis-ci.org/darothen/experiment)

**experiment** is designed to help you manage your modeling/data analysis workflows using [xarray][].

[xarray]: http://xarray.pydata.org/en/stable/

## Example Scenario

Suppose you've performed a set of climate model simulations with one particular model. In those simulations, you've looked at two emissions scenarios (a "high" and a "low" emissions case) and you've used three different values for some tuned parameter in the model (let's call them "x", "y", and "z"). Each simulation produces the same set of output tapes on disk, which you've conveniently arranged in the following hierarchical folder layout:

```
high_emis/
         /param_x
         /param_y
         /param_z
low_emis/
        /param_x
        /param_y
        /param_z
```

Each output file has a simple naming scheme which reflects the parameter choices, so for instance surface temperature output for one simulation is in a file named `low.x.TS.nc` under **low_emis/param_x/**.

The idea underpinning **experiment** is that it should be really easy to analyze this data, and you shouldn't have to spend time writing lots of boilerplate code to load and process your simulations. You went through the hassle to organize your data in a logical manner (which you're doing for reproducibility anyway, right?) - why not leverage that organization to help you out?

## Example Usage

**experiment** lets you describe how your data is organized on disk by defining `Case`s and an `Experiment`. In the example above, we have two `Case`s: an emissions scenario, and a set of values for a given parameter. We record this calling *Case* with a short name (alias), long-name, and set of values:

``` python
from experiment import Case

emis = Case("emis", "Emissions Scenario", ['low', 'high'])
param = Case("param", "Tuning Parameter", ['x', 'y', 'z'])
```

The values should correspond to how the output files (or folders) are labeled on disk, using any set of alphanumeric strings. For instance, if the parameter values were 1.5, 2.0, and 4.0, you could encode them as string versions of those numbers, or something like "1p5", "2p5", and "4p5" if that's more convenient.

A collection of `Case`s constitutes an `Experiment`. An `Experiment` defines where the data exists on disk, and uses simple Python format strings to define the naming schema for the directory structure and files. In our example, the **case_path** is a tree-structure, "emis_{emis}/param_{param}", where the curly-braced parameters correspond to the short names of the `Case`s we previously defined. At each of these directories, we have files which look like "{emis}.{param}.\_\_\_.nc". The "\_\_\_" is a placeholder for some identifying label (usually a variable name, if you've saved your data in timeseries format, or a timestamp if in timeslice format), and the surrounding bits (*including* the ".") are an **output_prefix** and **output_suffix**, respectively.

Using this information, we can create an `Experiment` to access our data:

``` python
from experiment import Experiment

my_experiment = Experiment(
    name='my_climate_experiment',
    cases=[emis, param],
    data_dir='/path/to/my/data',
    case_path="emis_{emis}/param_{param}",
    output_prefix="{emis}.{param}.",
    output_suffix=".nc"
)
```

*my_experiment* has useful helper methods which let you quickly construct filenames to individual parts of your dataset, or iterate over different components.

The real advantage that **experiment** provides is its flexibility in defining the paths to your data. You can use almost any naming/organizational scheme, such as:

- a single folder with all the metadata contained in the filenames
- hierarchical folders but incomplete (or missing) metadata in filenames
- data stored in different places on disk or a cluster

In the latter case, you could point an `Experiment` to an arbitrary **case_path**, and build a symlinked hierarchy to your data.

## Loading data

The point behind having an `Experiment` object is to be able to quickly load your data. We can do that with the `Experiment.load()` function, which will return a dictionary of `Dataset`s, each one indexed by a tuple of the case values corresponding to it.

``` python
data = my_experiment.load("TS")
```

This is useful for organizing your data for further analysis. You can pass a function to the **preprocess** kwarg, and it will be applied to each loaded `Dataset` before loaded into memory. Optionally, you can also pass **master=True** to the `load()` function, which will concatenate the data on new dimensions into a "master" dataset that contains all of your data. Preprocessing is applied before the dataset is concatenated, to reduce the memory overhead.

## Saving Experiments

An `Experiment` can also be directly read from disk in **.yml** format. The case here would serialize to

``` yaml
---
# Sample Experiment configuration
name: my_experiment
cases:
    emis:
        longname: Emissions Scenario
        vals:
            - high
            - low
    param:
        longname: Tuning Parameter
        vals: [x, y, z]
data_dir: /path/to/my/data
# Be sure to use single-quotes here so you don't have to escape the
# braces
case_path: 'emis_{emis}/param_{param}'
output_prefix: '{emis}.{param}.'
output_suffix: '.nc'
...
```

which can be directly loaded into an `Experiment` via

``` python
my_experiment = Experiment.load("my_experiment.yml")
```
