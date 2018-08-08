import codecs
from os import path
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

with codecs.open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESC = f.read()

INSTALL_DEPS = [
    'cwltool==1.0.20180820141117',
    'Flask==1.0.2',
    'Flask-Cors==3.0.6',
    'aap-client-python==0.1.4',
    'cryptography==2.3.1',
    'PyYAML==3.13',
    'future==0.16.0',
    'SQLAlchemy==1.2.11',
    'psycopg2==2.7.5',
    'SQLAlchemy-Utils==0.33.3',
    'ruamel.yaml<=0.15.51'
]
TEST_DEPS = [
    'pytest'
]
DEV_DEPS = []

setup(
    name='workflow_service',

    # https://pypi.python.org/pypi/setuptools_scm
    use_scm_version=True,

    description='Workflow runner service',
    long_description=LONG_DESC,

    url="https://github.com/psafont/workflow-service",

    author='Common workflow language working group, Pau Ruiz Safont',
    author_email='psafont@ebi.ac.uk',

    license='Apache 2.0',

    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='wes workflow cwl flask',

    packages=find_packages(exclude=['tests', 'instance', 'queries']),

    install_requires=INSTALL_DEPS,

    setup_requires=['setuptools_scm'],

    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4.0',

    extras_require={
        'test': TEST_DEPS,
        'dev': DEV_DEPS
    },

    entry_points={
        'console_scripts': ["wes-server=workflow_service.server:main"]
    },

    zip_safe=True)
