""" EEA RDF Marshaller Installer
"""
import os
from setuptools import setup, find_packages

name = "eea.rdfmarshaller"
path = name.split('.') + ['version.txt']
version = open(os.path.join(*path)).read().strip()

setup(name=name,
      version=version,
      description="RDF marshaller for Plone",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='RDF linkeddata lod semanticweb plone',
      author='European Environment Agency',
      author_email='webadmin@eea.europa.eu',
      url='http://svn.eionet.europa.eu/projects/'
          'Zope/browser/trunk/eea.rdfmarshaller',
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
          'Products.ATVocabularyManager',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
