from setuptools import setup, find_packages


setup(
    zip_safe=False,
    name="qtile_yammer_checker",
    version="0.1",
    packages=find_packages(),
    install_requires=["yampy", "oauth2client"])
