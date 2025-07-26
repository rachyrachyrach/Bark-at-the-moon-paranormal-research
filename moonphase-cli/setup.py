from setuptools import setup

setup(
    name='moonphase-cli',
    version='0.1',
    py_modules=['moonphase'],
    install_requires=['requests', 'click', 'rich'],
    entry_points={
        'console_scripts': [
            'moonphase=moonphase:main',
        ],
    },
)