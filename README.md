# experiment: Managing modeling experiment output

[![Build Status](https://travis-ci.org/darothen/experiment.svg?branch=master)](https://travis-ci.org/darothen/experiment)

**experiment** is designed to help you manage your modeling/data analysis workflows using [xarray][].

## Example

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




[xarray]: http://xarray.pydata.org/en/stable/
