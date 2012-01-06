#!/usr/bin/env python

import os
from setuptools import setup, find_packages

install_requires = [
    'Django>=1.3',
    'line_profiler==1.0b3',
]

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == "":
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

package_dir = "django_sense"

packages = []
for dirpath, dirnames, filenames in os.walk(package_dir):
    # ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith("."):
            del dirnames[i]
    if "__init__.py" in filenames:
        packages.append(".".join(fullsplit(dirpath)))

setup(
  name='django-sense',
  keywords="django sense profile",
  version='0.1',
  description='Profiling tools for Django',
  author='Stephen Diehl',
  author_email='stephen.m.diehl@gmail.com',
  license='MIT',
  url='https://github.com/sdiehl/django-sense',
  install_requires=install_requires,
  packages=find_packages(),
  package_data={
    'django_sense': ['django_sense']
  },
  include_package_data=True,
)
