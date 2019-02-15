""" This module contains helper functions and utilities for generating plugin.xml files from a click CLI.
"""
import click
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom.minidom import parseString
import hydra_base
import os


# Special argument names (keys) to be used as click options mapped
# to types defined in Hydra/HWI (values)
ARGTYPES = {
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


def make_plugins(group, shell, docker_image=None):
    """ Generator of plugin XML data from the hydra_pywr CLI. """
    for name, command in group.commands.items():

        try:
            hydra_app_category = command.hydra_app_category
        except AttributeError:
            hydra_app_category = False

        if not hydra_app_category:
            continue

        # Create plugin data for each sub-command of the group.
        data = make_plugin(command, hydra_app_category, shell, docker_image=docker_image)
        # Convert the data to etree ElementTree
        xml = plugin_to_xml(data)
        yield name, xml


def make_plugin(command, category, shell, docker_image=None):
    """ Make an individual plugin XML definition from a `click.Command`. """

    name = command.hydra_app_name
    if name is None:
        name = command.short_help

    if name is None:
        name = command.name

    plugin = {
        'plugin_name': name,
        'plugin_dir': '',
        'plugin_description': command.help,
        'plugin_category': category,
        'plugin_location': '.',
        'plugin_nativelogextension': '.log',
        'plugin_nativeoutputextension': '.out',
        'smallicon': None,
        'largeicon': None,
        'plugin_epilog': command.epilog,
        'mandatory_args': [arg for arg in make_args(command)],
        'non_mandatory_args': [arg for arg in make_args(command, required=False)],
        'switches': []
    }

    if docker_image is None:
        plugin.update({
            'plugin_command': '{}'.format(command.name),
            'plugin_shell': shell,
        })
    else:
        plugin.update({
            'plugin_command': '{} {}'.format(shell, command.name),
            'plugin_shell': 'docker',
            'plugin_docker_image': docker_image,
        })

    return plugin


def make_args(command, required=True):
    """ Generate argument definitions for each parameter in command. """
    for param in command.params:
        if not isinstance(param, (click.Argument, click.Option)):
            continue

        if param.required != required:
            continue

        arg = {
            'name': param.name,
            'switch': '--' + param.name.replace('_', '-'),
            'multiple': 'Y' if param.multiple else 'N',
        }

        # Add argtype if matches a given type.
        try:
            arg['argtype'] = ARGTYPES[param.name]
        except KeyError:
            pass

        yield arg


def plugin_to_xml(data):
    """ Convert plugin definition to ElementTree. """
    root = ET.Element('plugin_info')

    for key, value in data.items():
        e = ET.SubElement(root, key, )

        if key in ('mandatory_args', 'non_mandatory_args'):
            for arg in value:
                arg_element = ET.SubElement(e, 'arg')
                for arg_key, arg_value in arg.items():
                    arg_sub_element = ET.SubElement(arg_element, arg_key)
                    arg_sub_element.text = arg_value
        else:
            e.text = value

    return root


def write_plugins(plugins, app_name):
    """ Write the generated plugins to XML files. """
    base_plugin_dir = Path(hydra_base.config.get('plugin', 'default_directory'))
    base_plugin_dir = base_plugin_dir.joinpath(app_name)

    if not base_plugin_dir.exists():
        base_plugin_dir.mkdir(parents=True, exist_ok=True)

    for name, element in plugins:
        plugin_path = os.path.join(base_plugin_dir, name)

        if not os.path.exists(plugin_path):
            os.mkdir(plugin_path)

        with open(os.path.join(plugin_path, 'plugin.xml'), 'w') as fh:
            reparsed = parseString(ET.tostring(element, 'utf-8'))
            fh.write(reparsed.toprettyxml(indent="\t"))
