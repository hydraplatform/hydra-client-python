from hydra_client.connection import JSONConnection
from hydra_base_fixtures import *


def test_local_connection(session):
    """ Test a direct connection to hydra-base. """

    connection = JSONConnection(app_name='Test application.')
    connection.login()
    # Check login
    assert connection.user_id is not None

    # Get my own projects
    #The UID argument ere is the user whose projects are being requested
    projects = connection.get_projects(connection.user_id)
    # There should be no projects in this new DB.
    assert len(projects) == 0
