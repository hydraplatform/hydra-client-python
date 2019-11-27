from hydra_client.connection import RemoteJSONConnection
from hydra_base_fixtures import *
import pytest

# Mark this whole module as soap tests
pytestmark = pytest.mark.webtest


def test_remote_connection(session):
    """ Test a direct connection to hydra-base. """
    connection = RemoteJSONConnection(url="http://localhost:8080", app_name="Test Application")
    #connection.login(username="root", password="")
    connection.login()

    # Get my own projects
    #The UID argument ere is the user whose projects are being requested
    #projects = connection.get_projects({'uid':connection.user_id})
    projects = connection.get_projects()
    assert len(projects) >= 0
    # There could be projects in the DB, as the DB has been created by the server

    #and so we don't know what's in it -- so there should be at least 0 projects.
    project_not_a_user = connection.get_projects(user_id=999)
    assert len(project_not_a_user) == 0
