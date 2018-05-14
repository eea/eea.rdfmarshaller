==================
EEA RDF Marshaller
==================
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.rdfmarshaller/develop
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.rdfmarshaller/job/develop/display/redirect
  :alt: develop
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.rdfmarshaller/master
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.rdfmarshaller/job/master/display/redirect
  :alt: master

Export any Archetype content to RDF.
It provides a few general adaptors for ATContentTypes and ATVocabularyManager.
You can then look in eea.soer to find out how to customize these adaptors
for your own RDF schemas and own content types.

Contents
========

.. contents::

Install
=======

- Add eea.rdfmarshaller to your eggs section in your buildout and re-run buildout.
  You can download a sample buildout from
  https://github.com/eea/eea.rdfmarshaller/tree/master/buildouts/plone4
- Install *EEA RDF Marshaller* within Site Setup > Add-ons

Getting started
===============

See `marshaller.txt <https://github.com/eea/eea.rdfmarshaller/blob/master/eea/rdfmarshaller/marshall.txt>`_

Source code
===========

- Latest source code (Plone 4 compatible):
  https://github.com/eea/eea.rdfmarshaller


Copyright and license
=====================
The Initial Owner of the Original Code is European Environment Agency (EEA).
All Rights Reserved.

The EEA Progress Bar (the Original Code) is free software;
you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation;
either version 2 of the License, or (at your option) any later
version.

More details under docs/License.txt


Funding
=======

EEA_ - European Environment Agency (EU)

.. _EEA: http://www.eea.europa.eu/
