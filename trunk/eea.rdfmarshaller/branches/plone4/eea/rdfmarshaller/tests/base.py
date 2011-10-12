""" Base module """
from Products.CMFCore.utils import getToolByName
from Products.PloneTestCase import PloneTestCase
from Products.PloneTestCase.layer import onsetup
from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.ATVocabularyManager.config import TOOL_NAME as VOCABTOOL
import sys, logging
from Products.CMFPlone.log import logger
import eea.rdfmarshaller

PloneTestCase.installProduct('ATVocabularyManager')

PRODUCTS = ['ATVocabularyManager']
PROFILES = ['eea.rdfmarshaller:default']

@onsetup
def setup_rdfmarshaller():
    """ Setup """
    fiveconfigure.debug_mode = True
    zcml.load_config('configure.zcml', eea.rdfmarshaller)
    zcml.load_config('testing.zcml', eea.rdfmarshaller) 
    fiveconfigure.debug_mode = False

setup_rdfmarshaller()
PloneTestCase.setupPloneSite(products=PRODUCTS,  
        extension_profiles=['eea.rdfmarshaller:testfixture']) 
#PloneTestCase.setupPloneSite(extension_profiles=('eea.rdfmarshaller:default',))

class FunctionalTestCase(PloneTestCase.FunctionalTestCase):
    """ Functional Test Case """

    def afterSetUp(self):
        """ After setup """
        self.setRoles(['Manager'])


    def enableDebugLog(self):
        """ Enable context.plone_log() output from Python scripts """
        logger.root.setLevel(logging.WARN)
        logger.root.addHandler(logging.StreamHandler(sys.stdout))

    def setupVocabularies(self):
        """ Setup vocabularies """
        portal = self.portal
        atvm = getToolByName(portal, VOCABTOOL, None)
        if atvm is None:
            return
        vocabs =  {
            'eea.rdfmarshaller.vocab.testing': (
              (u'air pollution', "Air pollution"),
              (u'climate change', "Climate change mitigation"),
              (u'biodiversity', "Nature protection and biodiversity"),
              (u'land', "Land use"),
              (u'freshwater', "Freshwater"),
              (u'waste', "Waste"),
             ),
            }

        #wftool = portal.portal_workflow 
        for vkey in vocabs.keys():
            atvm.invokeFactory('SimpleVocabulary', vkey)
            simple = atvm.getVocabularyByName(vkey)
            for (key, val) in vocabs[vkey]:
                simple.addTerm(key, val)
                term = simple[key] 
                #wftool.doActionFor(term, 'publish') 
