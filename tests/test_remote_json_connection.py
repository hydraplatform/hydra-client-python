from hydra_client.connection import RemoteJSONConnection
from hydra_base_fixtures import *


def test_local_connection(session):
    """ Test a direct connection to hydra-base. """

    connection = RemoteJSONConnection(url="http://localhost:8080", app_name="Test application.")
    #connection.login(username="root", password="")
    connection.login()

    # Get my own projects
    #The UID argument ere is the user whose projects are being requested
    connected_user = connection.whoami()

    assert connection.user_id == connected_user.id

    # Get my own projects
    #The UID argument ere is the user whose projects are being requested
    projects = connection.get_projects({'uid':connection.user_id})

    # There could be projects in the DB, as the DB has been created by the server
    #and so we don't know what's in it -- so there should be at least 0 projects.
    assert len(projects) >= 0
