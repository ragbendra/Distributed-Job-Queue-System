from setuptools import setup, find_packages

setup(
    name="jobqueue-shared",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pika>=1.3.0",
        "redis>=5.0.0",
    ],
)
