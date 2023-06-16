from setuptools import setup, find_packages

setup(
    name='hydra-client',
    version='0.1.3',
    description='Client side libraries for Hydra.',
    author='Stephen Knox',
    author_email='stephen.knox@manchester.ac.uk',
    url='https://github.com/hydraplatform/hydra-client-python',
    packages=find_packages(),
    install_requires=['lxml', 'requests', 'cryptography'],
    entry_points='''
        [console_scripts]
        hydra-cli=hydra_client.cli:start_cli
        ''',

)
