from re import search
from setuptools import setup, find_packages


name = 'verarandom'

with open("README.md") as f:
    long_description = f.read()

with open(f'{name}/__init__.py') as f:
    version = search(r"__version__ = '(.*)'", f.read()).group(1)


setup(
    name=name,
    version=version,
    description='True random numbers in Python',
    author='Ali Ghahraei Figueroa',
    author_email='aligf94@gmail.com',
    url='https://github.com/AliGhahraei/verarandom',
    license='MIT',

    long_description=long_description,
    long_description_content_type="text/markdown",

    install_requires=['requests'],
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Topic :: Scientific/Engineering :: Mathematics',
    ],
)
