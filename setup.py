#!/usr/bin/env python

from setuptools import setup, find_packages

kwargs = {
    'name': 'catbird',
    'version': '0.0.1',
    'packages': find_packages(exclude=['tests*']),
    'author': 'Patrick Shriwise',
    'author_email': 'pshriwise@gmail.com',
    'download_url': 'https://github.com/pshriwise/catbird',
    'python_requires': '>=3.6',
    'extras_require': {
        'test': ['pytest']
    }
}

setup(**kwargs)
