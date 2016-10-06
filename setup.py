"""Installation script."""

from setuptools import setup


setup(
    name="chain",
    version="0.1.7",
    py_modules=["chain"],
    dependency_links=['git+https://github.com/AlanCristhian/name.git'],
    zip_safe=True,
    author="Alan Cristhian",
    author_email="alan.cristh@gmail.com",
    description="""Data transformation and data analysis by successive
                function calls and successive generator consumption""",
    license="MIT",
    keywords="data structure functional",
    url="https://github.com/AlanCristhian/chain",
)
