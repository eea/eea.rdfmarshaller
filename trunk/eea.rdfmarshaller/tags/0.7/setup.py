from setuptools import setup, find_packages
import os

author = "European Environment Agency"
name = "eea.rdfmarshaller"
path = name.split('.') + ['version.txt']
version = open(os.path.join(*path)).read().strip()

setup(name=name,
      version=version,
      description="RDF marshaller for Plone",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='RDF linkeddata lod semanticweb plone',
      author=author,
      author_email='webadmin@eea.europa.eu',
      url='http://svn.eionet.europa.eu/projects/Zope',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['eea'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'uuid',
          'surf',
          'surf.rdflib',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
