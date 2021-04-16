
import click
import json
import os
import hydra_base as hb
from hydra_client.connection import JSONConnection
from hydra_client.click import hydra_app, make_plugins, write_plugins
import getpass
import difflib
from collections import defaultdict
import logging
LOG = logging.getLogger('hydra_utilities')

def get_client(hostname, **kwargs):
    return JSONConnection(app_name='Hydra Base Utilities', db_url=hostname, **kwargs)


def get_logged_in_client(context, user_id=None):
    session = context['session']
    client = get_client(context['hostname'], session_id=session, user_id=user_id)
    if client.user_id is None:
        client.login(username=context['username'], password=context['password'])
    return client


def start_cli():
    cli(obj={}, auto_envvar_prefix='HYDRA_UTILITIES')


@click.group()
@click.pass_obj
@click.option('-u', '--username', type=str, default=None)
@click.option('-p', '--password', type=str, default=None)
@click.option('-h', '--hostname', type=str, default=None)
@click.option('-s', '--session', type=str, default=None)
def cli(obj, username, password, hostname, session):
    """ CLI for the Pywr-Hydra application. """

    obj['hostname'] = hostname
    obj['username'] = username
    obj['password'] = password
    obj['session'] = session


@hydra_app(category='admin', name='Remove Duplicate Attributes')
@cli.command(name='remove-duplicate-attributes',
    context_settings=dict( ignore_unknown_options=True, allow_extra_args=True))
@click.pass_obj
def delete_duplicate_attributes(obj):
    """ Remove duplicate attributes """
    client = get_logged_in_client(obj)

    client.delete_all_duplicate_attributes()

    LOG.info("Duplicate attributes deleted.")

@hydra_app(category='admin', name='Remove Duplicate Resource Attributes')
@cli.command(name='remove-duplicate-resource-attributes',
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_obj
def delete_duplicate_resource_attributes(obj):
    """ Remove duplicate resource attributes """
    client = get_logged_in_client(obj)

    client.delete_duplicate_resourceattributes()

    LOG.info("Duplicate resource attributes deleted.")

@hydra_app(category='admin', name='Set roles and permissions')
@cli.command(name='set-roles-and-permissions',
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_obj
def set_roles_and_permissions(obj):
    """ Set roles and permissions, as defined in the hydra base permissions file"""
    hb.db.connect()

    hb.util.hdb.create_default_users_and_perms()

    hb.db.commit_transaction()

    LOG.info("Roles and permissions set")

@hydra_app(category='admin', name='Initialise the database with all the required default data')
@cli.command(name='initialise-db',
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_obj
def initialise_db(obj):
    """ Set roles and permissions, as defined in the hydra base permissions file"""
    hb.db.connect()

    hb.util.hdb.create_default_users_and_perms()
    hb.util.hdb.create_default_units_and_dimensions()
    hb.util.hdb.make_root_user()
    hb.util.hdb.create_default_net()

    hb.db.commit_transaction()

    LOG.info("Roles and permissions set")


@hydra_app(category='admin', name='Change Password')
@cli.command(name='update-user-password')
@click.pass_obj
def update_user_password(obj):
    """ Set roles and permissions, as defined in the hydra base permissions file"""

    client = get_logged_in_client(obj)

    hb.db.connect()

    username = input('Username to Change: ')

    user = client.get_user_by_name(username)

    if user is None:
        print(f"User {username} not found.")

    pwd1 = getpass.getpass(prompt='Password: ')
    pwd2 = getpass.getpass(prompt='Confirm Password: ')

    if pwd1 != pwd2:
        print("Passwords to not match. Returning.")
        return

    client.update_user_password(user.id, pwd1)

    LOG.info("Password Changed")

@hydra_app(category='network-utility', name='Compare two scenarios. These can be in different networks')
@cli.command(name='compare-scenarios',
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))

@click.option('-s1', '--scenario-1', type=int, help="""Scenario 1 ID""")
@click.option('-s2', '--scenario-2', type=int, help="""Scenario 2 ID""")
@click.option('--allow-different-networks', is_flag=True, default=False,
              help="""Allow different networks""")
@click.option('--include-results', is_flag=True, default=False,
              help="""Include Results""")
@click.option('--show-diff', is_flag=True, default=False,
              help="""Show the difference between the two values""")
@click.pass_obj
def compare_scenarios(obj, scenario_1, scenario_2, allow_different_networks, show_diff, include_results):
    """ Compare 2 hydra scenarios """

    client = get_logged_in_client(obj)

    comparison = client.compare_scenarios(scenario_1, scenario_2, allow_different_networks, include_results=include_results)

    diff_summary = defaultdict(lambda: {})
    for rs in comparison['resourcescenarios']:
        diff_summary[rs['resource_name']][rs.attr_name] = None
        d1 = rs['scenario_1_dataset']
        v1 = None
        if d1 is not None:
            v1 = d1['value']

        d2 = rs['scenario_2_dataset']
        v2 = None
        if d2 is not None:
            v2 = d2['value']

        if v1 is not None and v2 is not None:
            if show_diff == True:
                diff = list(difflib.ndiff(v1, v2))
            else:
                diff = f"Values are different"
        elif v1 is not None and v2 is None:
            diff = f"In {scenario_1}, not in {scenario_2}"
        elif v1 is None and v2 is not None:
            diff = f"In {scenario_2}, not in {scenario_1}"

        diff_summary[rs['resource_name']][rs.attr_name] = diff

    print(json.dumps(diff_summary, sort_keys=False, indent=4))
