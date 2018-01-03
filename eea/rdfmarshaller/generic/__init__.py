""" Generic adapters
"""

from eea.rdfmarshaller.interfaces import IPublisherOrganisation
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapts
from zope.interface import implements


class GenericPublisherOrganisation(object):
    implements(IPublisherOrganisation)
    adapts(IPloneSiteRoot)

    def __init__(self, portal):
        self.portal = portal

        self.logo_url = portal.absolute_url() + '/logo.png'
        self.logo_width = ""
        self.logo_height = ""
        self.name = portal.getProperty('title')
