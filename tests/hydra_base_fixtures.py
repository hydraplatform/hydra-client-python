from hydra_base.db import DeclarativeBase as _db
from hydra_base.util.hdb import create_default_users_and_perms, make_root_user
from hydra_base.lib.objects import JSONObject
import hydra_base
from hydra_base import config
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

from hydra_pywr.template import generate_pywr_attributes, generate_pywr_template

global user_id
user_id = config.get('DEFAULT', 'root_user_id', 1)


@pytest.fixture
def db_backend(request):
    return 'sqlite'

@pytest.fixture()
def testdb_uri(db_backend):
    if db_backend == 'sqlite':
        # Use a :memory: database for the tests.
        return 'sqlite://'
    elif db_backend == 'postgres':
        # This is designed to work on Travis CI
        return 'postgresql://postgres@localhost:5432/hydra_base_test'
    elif db_backend == 'mysql':
        return 'mysql+mysqlconnector://root@localhost/hydra_base_test'
    else:
        raise ValueError('Database backend "{}" not supported when running the tests.'.format(db_backend))


@pytest.fixture(scope='function')
def engine(testdb_uri):
    engine = create_engine(testdb_uri)
    return engine


@pytest.fixture(scope='function')
def db(engine, request):
    """ Test database """
    _db.metadata.create_all(engine)
    return _db


@pytest.fixture(scope='function')
def session(db, engine, request):
    """Creates a new database session for a test."""
    db.metadata.bind = engine

    DBSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    # A DBSession() instance establishes all conversations with the database
    # and represents a "staging zone" for all the objects loaded into the
    # database session object. Any change made against the objects in the
    # session won't be persisted into the database until you call
    # session.commit(). If you're not happy about the changes, you can
    # revert all of them back to the last commit by calling
    # session.rollback()
    session = DBSession()

    # Patch the global session in hydra_base
    hydra_base.db.DBSession = session

    # Now apply the default users and roles
    create_default_users_and_perms()
    make_root_user()

    # Add some users
    create_user("UserA")
    create_user("UserB")
    create_user("UserC")

    yield session

    # Tear down the session

    # First make sure everything can be and is committed.
    session.commit()
    # Finally drop all the tables.
    hydra_base.db.DeclarativeBase.metadata.drop_all()


@pytest.fixture()
def session_with_pywr_template(session):

    attributes = [JSONObject(a) for a in generate_pywr_attributes()]

    # The response attributes have ids now.
    response_attributes = hydra_base.add_attributes(attributes)

    # Convert to a simple dict for local processing.
    attribute_ids = {a.attr_name: a.attr_id for a in response_attributes}

    template = generate_pywr_template(attribute_ids)

    hydra_base.add_template(JSONObject(template))

    yield session


def create_user(name):

    existing_user = hydra_base.get_user_by_name(name)
    if existing_user is not None:
        return existing_user

    user = JSONObject(dict(
        username = name,
        password = "password",
        display_name = "test useer",
    ))

    new_user = JSONObject(hydra_base.add_user(user, user_id=user_id))

    #make the user an admin user by default
    role =  JSONObject(hydra_base.get_role_by_code('admin', user_id=user_id))

    hydra_base.set_user_role(new_user.id, role.role_id, user_id=user_id)

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
        p = JSONObject(hydra_base.get_project_by_name(name, user_id=user_id))
        return p
    except Exception:
        project = JSONObject()
        project.name = name
        project.description = "Project which contains all unit test networks"
        project = JSONObject(hydra_base.add_project(project, user_id=user_id))
        hydra_base.share_project(project.id,
                                 ["UserA", "UserB", "UserC"],
                                 'N',
                                 'Y',
                                 user_id=user_id)

        return project

@pytest.fixture()
def root_user_id():
    return user_id