from setuptools import setup

setup(
    name='htmd',
    version='1.0',
    packages=['htmd'],
    include_package_data=True,
    install_requires=[
        'flask',
        'Flask-FlatPages',
        'Frozen-Flask',
        'click',
        'htmlmin'
    ],
    entry_points='''
        [console_scripts]
        htmd=htmd.cli:cli
    ''',
    zip_safe=False,  # Required to have template files as files (not strings)
)
