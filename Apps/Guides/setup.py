"""
Setup script for the TravelGuide project.
This allows the project to be installed in development mode.
"""
from setuptools import setup, find_packages

setup(
    name="travelguide",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # List your project's dependencies here
        'Django>=5.0',
        # Add other dependencies as needed
    ],
    python_requires='>=3.8',
)
