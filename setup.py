from setuptools import setup

setup(
    name='awsume-console-plugin',
    version='1.0.2',
    entry_points={
        'awsume': [
            'console = console'
        ]
    },
    author='Trek10, Inc',
    author_email='package-management@trek10.com',
    py_modules=['console'],
)
