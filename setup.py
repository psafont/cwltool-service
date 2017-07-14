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
          'connexion',
          'bravado',
          'pre-commit',
          'PyYAML',
          'future',
          'flask-jwt-extended'
      ],
      setup_requires=['pytest-runner'],
      test_suite='tests',
      tests_require=[
          'pytest',
          'unittest2',
          'mock'
      ],
      entry_points={
          'console_scripts': ["wes-server=wes_service:main",
                              "wes-client=wes_client:main"]
      },
      zip_safe=True)
