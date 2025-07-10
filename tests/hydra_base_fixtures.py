from hydra_client.objects import ExtendedDict
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

global user_id
user_id = os.getenv('HYDRA_DEFAULT_ROOT_USER_ID', 1)


global root_username
root_username = os.getenv('HYDRA_DEFAULT_ROOT_USERNAME', 'root')

global root_password
root_username = os.getenv('HYDRA_DEFAULT_ROOT_PASSWORD', 'root')

global hostname
hostname = os.getenv('HYDRA_DEFAULT_HOSTNAME', 'http://localhost:8080')

global remote_client
remote_client = RemoteJSONConnection(hostname)
remote_client.login(hostname)

@pytest.fixture()
def session_with_pywr_template(session):

    attributes = [ExtendedDict(a) for a in generate_pywr_attributes()]

    # The response attributes have ids now.
    response_attributes = remoteclient.add_attributes(attributes)

    # Convert to a simple dict for local processing.
    attribute_ids = {a.attr_name: a.attr_id for a in response_attributes}

    template = generate_pywr_template(attribute_ids)

    remoteclient.add_template(ExtendedDict(template))

    yield session


def create_user(name):

    existing_user = remote_client.get_user_by_name(name)
    if existing_user is not None:
        return existing_user

    user = dict(
        username = name,
        password = "password",
        display_name = "test useer",
    )

    new_user = remote_client.add_user(user, user_id=user_id)

    #make the user an admin user by default
    role =  remote_client.get_role_by_code('admin', user_id=user_id)
    remote_client.set_user_role(new_user.id, role.id, user_id=user_id)

    return new_user


@pytest.fixture()
def projectmaker():
    class ProjectMaker:
        def create(self, name=None):
            if name is None:
                name = 'Project %s' % (datetime.datetime.now())
            return create_project(name=name)

    return ProjectMaker()


def create_project(name=None):
    if name is None:
        name = "Unittest Project"

    try:
        p = remote_client.get_project_by_name(name, user_id=user_id)
        return p
    except Exception:
        project = {
            'name' :name,
            'description': "Project which contains all unit test networks"
        }
        project = remote_client.add_project(project, user_id=user_id)
        remote_client.share_project(project.id,
                                 ["UserA", "UserB", "UserC"],
                                 'N',
                                 'Y',
                                 user_id=user_id)

        return project

@pytest.fixture()
def root_user_id():
    return user_id
