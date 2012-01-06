#!/usr/bin/env python

from setuptools import setup, find_packages

install_requires = [
    'Django>=1.3',
    'line_profiler==1.0b3',
]

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
    'django_sense': ['templates/django_sense/*.html']
  },
  zip_safe=False,
  include_package_data=True,
)
