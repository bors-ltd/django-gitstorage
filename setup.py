# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(name="django-gitstorage",
      description="Django storage and views to browse a Git repository",
      version="1.0",
      author="Bors Ltd",
      author_email="gitstorage@bors-ltd.fr",
      license="GPL3",
      long_description=open("README.rst").read(),
      url="https://github.com/bors-ltd/django-gitstorage",
      packages=find_packages(),
      include_package_data=True,
      setup_requires=['distribute'],
      install_requires=open("requirements.txt").readlines())
