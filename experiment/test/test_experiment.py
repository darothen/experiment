
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

from itertools import product
from experiment import Experiment, Case


case_emis = \
    Case('emis', 'Emissions Scenario', ['policy', 'no_policy', 'weak_policy'])
case_model_config = \
    Case('model_config', 'Model configuration',
         ['no_clouds', 'no_sun', 'no_sun_no_clouds'])
default_exp_kws = dict(
    name='my_experiment',
    cases = [case_emis, case_model_config],
    timeseries=True, data_dir='/path/to/my/data',
    case_path='{emis}/{model_config}',
    output_prefix='experiment_{emis}_{model_config}.data.',
    output_suffix='.tape.nc',
    validate_data=False
)

my_experiment = Experiment(**default_exp_kws)
def make_exp(**kwargs):
    kws = dict(default_exp_kws)
    kws.update(**kwargs)
    return Experiment(**kws)

class TestExperiment(unittest.TestCase):

    def test_repr(self):
        # Lazy hack because the indentation/newlines were messing things up
        expected = "my_experiment -\n   * emis (Emissions Scenario):  [policy, no_policy, weak_policy]\n   * model_config (Model configuration):  [no_clouds, no_sun, no_sun_no_clouds]"
        actual = repr(my_experiment)

        print(expected)
        print(actual)
        self.assertEqual(expected, actual)

    def test_case_attrs(self):

        case_list = [case_emis, case_model_config]

        # Cases property
        self.assertEqual(my_experiment.cases,
                         [case.shortname for case in case_list])

        # itercases generator
        actual_cases = [(case.shortname, case.longname, case.vals)
                        for case in case_list]
        exp_cases = [case for case in my_experiment.itercases()]
        self.assertEqual(exp_cases, actual_cases)

        # all_cases list
        actual_case_gen = product(*[case.vals for case in case_list])
        exp_case_gen = my_experiment.all_cases()
        for expected, actual in zip(exp_case_gen, actual_case_gen):
            self.assertEqual(expected, actual)

    def test_walk_cases_default(self):
        """ Walk cases when no case_path is provided - so bits are
        ordered in the order passed as cases """

        case_list = [case_emis, case_model_config]
        exp = my_experiment

        actual_paths = []
        for case_ordered in product(*[case.vals for case in case_list]):
            actual_paths.append(os.path.join(*case_ordered))
        exp_paths = exp._walk_cases()
        for expected, actual in zip(exp_paths, actual_paths):
            print(expected, actual)
            self.assertEqual(expected, actual)

    def test_walk_cases_custom(self):
        """ Walk cases when no case_path is provided - so bits are
        ordered in the order passed as cases """

        case_list = [case_emis, case_model_config]
        exp = my_experiment

        actual_paths = []
        for case_ordered in product(*[case.vals for case in case_list]):
            actual_paths.append(os.path.join(*case_ordered))
        exp_paths = exp._walk_cases()
        for expected, actual in zip(exp_paths, actual_paths):
            print(expected, actual)
            self.assertEqual(expected, actual)

        # Generic - no format arguments
        exp = Experiment("Test Experiment", case_list,
                         case_path="", validate_data=False)
        for p in exp._walk_cases():
            self.assertEqual(p, "")

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

    def test_case_path_formatting(self):
        """ Test passing different types of arguments to Experiment for
        creating case paths. """

        exp_all_str = make_exp(
            case_path="./", output_prefix="{emis}.{model_config}",
            output_suffix=".nc"
        )
        case_kws = dict(emis='policy', model_config='no_clouds')
        self.assertEqual("./",
                         exp_all_str.case_path(**case_kws))
        self.assertEqual("policy.no_clouds",
                         exp_all_str.case_prefix(**case_kws))
        self.assertEqual(".nc",
                         exp_all_str.case_suffix(**case_kws))

        exp_no_case_path = make_exp(
            output_prefix="{emis}.{model_config}",
            output_suffix=".nc"
        )
        case_kws = dict(emis='policy', model_config='no_clouds')
        self.assertEqual("policy/no_clouds",
                         exp_no_case_path.case_path(**case_kws))
        self.assertEqual("policy.no_clouds",
                         exp_no_case_path.case_prefix(**case_kws))
        self.assertEqual(".nc",
                         exp_no_case_path.case_suffix(**case_kws))

        def _prefix_func(emis, model_config):
            return "my_emis-{emis}.my_cfg-{model_config}".format(
                emis=emis, model_config=model_config
            )
        exp_prefix_func = make_exp(
            case_path="./", output_prefix=_prefix_func,
            output_suffix=".nc"
        )
        case_kws = dict(emis='policy', model_config='no_clouds')
        self.assertEqual("./",
                         exp_prefix_func.case_path(**case_kws))
        self.assertEqual("my_emis-policy.my_cfg-no_clouds",
                         exp_prefix_func.case_prefix(**case_kws))
        self.assertEqual(".nc",
                         exp_prefix_func.case_suffix(**case_kws))


        def _suffix_func(emis, model_config):
            return ".e1-{0}.ml2-{1}.txt".format(
                emis[0], model_config[-2:]
            )
        exp_suffix_func = make_exp(
            case_path="./", output_prefix="{emis}.{model_config}",
            output_suffix=_suffix_func
        )
        case_kws = dict(emis='policy', model_config='no_clouds')
        self.assertEqual("./",
                         exp_suffix_func.case_path(**case_kws))
        self.assertEqual("policy.no_clouds",
                         exp_suffix_func.case_prefix(**case_kws))
        self.assertEqual(".e1-p.ml2-ds.txt",
                         exp_suffix_func.case_suffix(**case_kws))


