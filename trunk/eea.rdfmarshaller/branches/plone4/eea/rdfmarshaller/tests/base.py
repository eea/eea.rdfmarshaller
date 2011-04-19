""" Base module """
from Products.CMFCore.utils import getToolByName
from Products.PloneTestCase import PloneTestCase
from Products.PloneTestCase.layer import onsetup
from Products.Five import zcml
from Products.Five import fiveconfigure

PRODUCTS = ['ATVocabularyManager']
PROFILES = ['eea.rdfmarshaller:default']

@onsetup
def setup_soer():
    """ Setup """
    fiveconfigure.debug_mode = True
    import Products.Five
    import eea.rdfmarshaller
    zcml.load_config('meta.zcml', Products.Five)
    zcml.load_config('configure.zcml', Products.Five)
    zcml.load_config('configure.zcml', eea.rdfmarshaller)
    fiveconfigure.debug_mode = False

    PloneTestCase.installProduct('Five')
    for product in PRODUCTS:
        PloneTestCase.installProduct(product)

setup_soer()
PRODUCTS.append('eea.rdfmarshaller')
PloneTestCase.setupPloneSite(products=PRODUCTS)


class FunctionalTestCase(PloneTestCase.FunctionalTestCase):
    """ Functional Test Case """

    def afterSetUp(self):
        """ After setup """
        self.setRoles(['Manager'])


    def enableDebugLog(self):
        """ Enable context.plone_log() output from Python scripts """
        import sys, logging
        from Products.CMFPlone.log import logger
        logger.root.setLevel(logging.WARN)
        logger.root.addHandler(logging.StreamHandler(sys.stdout))

    def setupVocabularies(self):
        """ Setup vocabularies """
        from Products.ATVocabularyManager.config import TOOL_NAME as VOCABTOOL
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

        for vkey in vocabs.keys():
            atvm.invokeFactory('SimpleVocabulary', vkey)
            simple = atvm.getVocabularyByName(vkey)
            for (key, val) in vocabs[vkey]:
                simple.addTerm(key, val)
