#!/usr/bin/env python
"""
    Common Workflow Language WES
"""
import os

from setuptools import setup, find_packages

SETUP_DIR = os.path.dirname(__file__)
README = os.path.join(SETUP_DIR, 'README.md')

setup(name='workflow_service',
      version='2.0',
      description='Workflow runner service',
      long_description=open(README).read(),
      author='Common workflow language working group, Pau Ruiz Safont',
      author_email='psafont@ebi.ac.uk',
      url="https://github.com/psafont/workflow-service",
      download_url="https://github.com/psafont/workflow-service",
      license='Apache 2.0',
      packages=find_packages(exclude=['tests']),
      install_requires=[
          'cwltool==1.0.20180116213856',
          'cwl-runner==1.0',
          'Flask==0.12.2',
          'Flask-Cors==3.0.3',
          'aap-client-python==0.1.1',
          'cryptography==2.1.4',
          'PyYAML==3.12',
          'future==0.16.0',
      ],
      extras_require={
          'test': ['pytest', 'unittest2'],
          'dev': ['pylint'],
      },
      entry_points={
          'console_scripts': ["wes-server=wes_server.server:main"]
      },
      zip_safe=True)
