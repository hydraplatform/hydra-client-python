from setuptools import setup, find_packages

setup(
    name='hydra-client-python',
    version='0.1',
    description='Client side libraries for Hydra.',
    author='Stephen Knox',
    author_email='stephen.knox@manchester.ac.uk',
    url='https://github.com/hydraplatform/hydra-client-python',
    packages=find_packages(),
    install_requires=['lxml', 'requests', 'suds-jurko', 'hydra-base'],
)
