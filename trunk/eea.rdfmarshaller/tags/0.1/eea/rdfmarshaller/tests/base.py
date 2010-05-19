import os
from Globals import package_home
from Products.PloneTestCase import PloneTestCase
from Products.PloneTestCase.layer import onsetup
from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.CMFPlone.interfaces import IPloneSiteRoot


PRODUCTS = []
PROFILES = ['eea.rdfmarshaller:default']

@onsetup
def setup_soer():
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
    
    def afterSetUp(self):
        self.setRoles(['Manager'])


