from setuptools import setup, find_packages

setup(
    name='mozilla_session_invalidation',
    version='1.0',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
