
from setuptools import setup, find_packages

setup(
    name='repyducible',
    version='0.1',
    description='Execute numerical experiments in a reproducible way',
    urls='https://github.com/room-10/Repyducible',
    author='Thomas Vogt',
    author_email='vogt@mic.uni-luebeck.de',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    keywords='numerics scientific experiments',
    packages=find_packages(),
    install_requires=['numpy','opymize'],
    project_urls={ 'Source': 'https://github.com/room-10/Repyducible/', },
)
