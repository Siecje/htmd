from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()


setup(
    name='htmd',
    version='1.2',
    packages=['htmd'],
    include_package_data=True,
    install_requires=requirements,
    entry_points='''
        [console_scripts]
        htmd=htmd.cli:cli
    ''',
    zip_safe=False,  # Required to have template files as files (not strings)
)
