from setuptools import setup

setup(
    name='tohtml',
    version='1.0',
    packages=['tohtml'],
    include_package_data=True,
    install_requires=[
        'flask',
        'Flask-FlatPages',
        'Frozen-Flask',
    ],
    entry_points='''
        [console_scripts]
        tohtml=tohtml.cli:main
    ''',
)
