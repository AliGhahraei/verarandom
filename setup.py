from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

setup(
    name='verarandom',
    version='1.1.0',
    description='True random numbers (provided by random.org) in Python',
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
