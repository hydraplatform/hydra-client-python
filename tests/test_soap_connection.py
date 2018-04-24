from hydra_client.connection import SOAPConnection
from hydra_base_fixtures import *
import logging

def test_local_connection():
    """ Test a direct connection to hydra-base. """

    logging.getLogger('suds').setLevel(logging.ERROR)
    logging.getLogger('suds.client').setLevel(logging.CRITICAL)
    logging.getLogger('suds.metrics').setLevel(logging.CRITICAL)

    connection = SOAPConnection(url="http://localhost:8080/soap", app_name='Test SOAP application.')
    connection.client.options.cache.clear()
    connection.login()
    # Check login
    assert connection.user_id is not None

    # Get my own projects
    projects = connection.client.service.get_projects(connection.user_id)
    # There should be no projects in this new DB.
    assert len(projects.ProjectSummary) >= 0
