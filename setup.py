#!/usr/bin/env python

from setuptools import setup, find_packages

kwargs = {
    'name': 'catbird',
    'version': '0.0.1',
    'packages': find_packages(exclude=['tests*']),
    'author': 'Patrick Shriwise',
    'author_email': 'pshriwise@gmail.com',
    'license' : 'MIT',
    'keywords': ['MOOSE'],
    'download_url': 'https://github.com/pshriwise/catbird',
    'url': 'https://github.com/pshriwise/catbird',
    'python_requires': '>=3.6',
    'install_requires': ['numpy'],
    'extras_require': {
        'test': ['pytest']
    }
}

setup(**kwargs)
