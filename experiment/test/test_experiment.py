
from copy import copy, deepcopy
from io import StringIO
from textwrap import dedent
try:
    import cPickle as pickle
except ImportError:
    import pickle

import os
import unittest
import yaml

from experiment import Experiment, Case


my_experiment = Experiment(
    name='my_experiment',
    cases = [
        Case('emis', 'Emissions Scenario', ['policy', 'no_policy', 'weak_policy']),
        Case('model_config', 'Model configuration',
             ['no_clouds', 'no_sun', 'no_sun_no_clouds']),
    ],
    timeseries=True, data_dir='/path/to/my/data',
    case_path='{emis}/{model_config}',
    output_prefix='experiment_{emis}_{model_config}.data.',
    output_suffix='.tape.nc',
    validate_data=False
)

class TestExperiment(unittest.TestCase):

    def test_repr(self):
        # Lazy hack because the indentation/newlines were messing things up
        expected = "my_experiment -\n   * emis (Emissions Scenario):  [policy, no_policy, weak_policy]\n   * model_config (Model configuration):  [no_clouds, no_sun, no_sun_no_clouds]"
        actual = repr(my_experiment)

        print(expected)
        print(actual)
        self.assertEqual(expected, actual)

    def test_validate(self):
        """ Test ability for Experiment to infer whether or not data corresponding
        to this experiment actual exist at the given path. """
        pass

    def test_exp_bits(self):
        """ Test if Experiment correctly provides the bits/kwargs corresponding
        to its configuration. """
        pass

    def test_from_yaml(self):
        """ Test reading a configuration from a YAML file on disk. """

        path_to_test = os.path.join(
            os.path.dirname(__file__), 'data', 'my_experiment.yaml'
        )
        with open(path_to_test, 'rb') as f:
            d = yaml.safe_load(f)
            print(d)

        exp = Experiment.from_yaml(path_to_test)

        self.assertEqual(repr(exp), repr(my_experiment))
