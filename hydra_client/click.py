import click
from pathlib import Path
import hydra_base
import os


# Special argument names (keys) to be used as click options mapped
# to types defined in Hydra/HWI (values)
HYDRA_ARGTYPES = {
    'network_id': 'network',
    'scenario_id': 'scenario',
    'project_id': 'project',
    'user_id': 'user',
    'filename': 'file',
}


def hydra_app(category='import', name=None):
    """A decorator to mark a click Command as a Hydra app."""
    def hydra_app_decorator(func):
        func.hydra_app_category = category
        func.hydra_app_name = name
        return func
    return hydra_app_decorator


def make_args(command):
    """ Generate argument definitions for each parameter in command. """
    for param in command.params:
        if not isinstance(param, (click.Argument, click.Option)):
            continue

        if param.type == click.BOOL:
            category = 'switches'
        elif param.required:
            category = 'mandatory_args'
        else:
            category = 'non_mandatory_args'

        arg = {
            'name': param.name,
            'switch': '--' + param.name.replace('_', '-'),
            'multiple': 'Y' if param.multiple else 'N',
        }

        # Add argtype if matches a given type.
        if param.name in HYDRA_ARGTYPES:
            arg['argtype'] = HYDRA_ARGTYPES[param.name]

        yield category, arg
