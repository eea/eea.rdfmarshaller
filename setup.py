""" EEA RDF Marshaller Installer
"""
import os

from setuptools import find_packages, setup

name = "eea.rdfmarshaller"
path = name.split('.') + ['version.txt']
version = open(os.path.join(*path)).read().strip()

setup(name=name,
      version=version,
      description="RDF marshaller for Plone",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Framework :: Zope2",
          "Framework :: Plone",
          "Framework :: Plone :: 4.0",
          "Framework :: Plone :: 4.1",
          "Framework :: Plone :: 4.2",
          "Framework :: Plone :: 4.3",
          "Programming Language :: Zope",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "License :: OSI Approved :: GNU General Public License (GPL)",
      ],
      keywords='EEA Add-ons Plone Zope',
      author='European Environment Agency: IDM2 A-Team',
      author_email='eea-edw-a-team-alerts@googlegroups.com',
      url='https://github.com/eea/eea.rdfmarshaller',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['eea'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Unidecode',
          'uuid',
          'surf>=1.1.9',
          'rdflib>=4.2.2',
          # 'surf.rdflib',
          'Products.ATVocabularyManager',
          'chardet',
          'eventlet',
          'rdflib_jsonld>=0.4.0',
          'collective.z3cform.datagridfield',
          'plone.formwidget.contenttree',
      ],
      extras_require={
          'test': [
              'Products.PloneTestCase',
              'plone.app.testing',
              'eea.depiction',
              'collective.z3cform.datagridfield',
          ]
      },
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
