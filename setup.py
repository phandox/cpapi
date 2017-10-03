from setuptools import setup

setup(
    # Application name:
    name='CPAPI',

    # Version number (initial):
    version='0.1.1',

    # Application author details:
    author='Joshua Hatter',
    author_email='jhatter@themadhatter.org',

    # Packages
    packages=['cpapiweb'],

    # Details
    url='https://github.com/themadhatterz/cpapi',
    download_url = 'https://github.com/themadhatterz/cpapi/archive/v0.1.0.tar.gz',

    # License
    license='LICENSE.txt',
    description='Web interface for interacting with Check Point Software Management API.',

    # Dependent packages
    install_requires=[
        'flask',
        'flask_nav',
        'requests',
    ],
)