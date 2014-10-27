from setuptools import setup

setup(
    name='to_html',
    version='1.0',
    py_modules=['to_html'],
    install_requires=[
        'flask',
        'Flask-FlatPages',
        'Frozen-Flask',
    ],
    entry_points='''
        [console_scripts]
        to_html=to_html:main
    ''',
)
