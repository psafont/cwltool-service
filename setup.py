#!/usr/bin/env python
"""
    Common Workflow Language WES
"""
import os

from setuptools import setup, find_packages

SETUP_DIR = os.path.dirname(__file__)
README = os.path.join(SETUP_DIR, 'README.md')

setup(name='cwltool_service',
      version='2.0',
      description='Common workflow language runner service',
      long_description=open(README).read(),
      author='Common workflow language working group',
      author_email='common-workflow-language@googlegroups.com',
      url="https://github.com/common-workflow-language/cwltool-service",
      download_url="https://github.com/common-workflow-language/cwltool-service",
      license='Apache 2.0',
      packages=find_packages(exclude=['tests']),
      # py_modules=["cwl_runner_wes"],
      install_requires=[
          'bravado==8.4.0',
          'connexion==1.1.9',
          'cwltool>=1.0.20170516234254',
          'cwl-runner==1.0',
          'Flask==0.12.2',
          'Flask-Cors==3.0.2',
          'Flask-JWT-Extended==3.1.1',
          'cryptography==2.0',
          'PyYAML==3.12',
          'future==0.16.0',
      ],
      extras_require={
          'test': ['pytest', 'unittest2'],
      },
      entry_points={
          'console_scripts': ["wes-server=cwltoolservice.cwl_flask:main",
                              "wes-client=wes_client:main"]
      },
      zip_safe=True)
