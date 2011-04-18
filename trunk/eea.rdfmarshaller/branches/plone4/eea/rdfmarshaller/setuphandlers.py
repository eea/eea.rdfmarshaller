""" Various setup
"""
import logging
from Products.CMFCore.utils import getToolByName

def setupVarious(context):
    """ Do some various setup.
    """
    if context.readDataFile('eea.rdfmarshaller.txt') is None:
        return

    logger = logging.getLogger("eea.rdfmarshaller")
    logger.info("Installing Products.Marshall")

    site = context.getSite()
    qinstaller = getToolByName(site, 'portal_quickinstaller')
    qinstaller.installProduct('Marshall')
