from setuptools import setup

setup(
    name='awsume-console-plugin',
    entry_points={
        'awsume': [
            'console = console'
        ]
    },
    py_modules=['console'],
)
