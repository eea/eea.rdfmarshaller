""" testing  """
from plone.app.testing import (PLONE_FIXTURE, FunctionalTesting,
                               IntegrationTesting, PloneSandboxLayer)

HAS_DEXTERITY = True
try:
    import plone.dexterity as HAS_DEXTERITY
except ImportError:
    HAS_DEXTERITY = False


class Fixture(PloneSandboxLayer):
    """ Fixture """

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """ Set up Zope """
        # Load ZCML
        import eea.rdfmarshaller
        import plone.dexterity
        import plone.app.textfield

        # needed for Dexterity FTI
        self.loadZCML(package=plone.dexterity)

        # needed for DublinCore behavior
        self.loadZCML(package=plone.app.dexterity)

        # needed to support RichText in testpage
        self.loadZCML(package=plone.app.textfield)

        self.loadZCML(package=eea.rdfmarshaller)
        self.loadZCML(package=eea.rdfmarshaller.licenses,
                      name="licenseviewlet.zcml")

        if HAS_DEXTERITY:
            from eea.rdfmarshaller import dexterity
            self.loadZCML(package=dexterity)

        self.loadZCML(package=eea.rdfmarshaller, name='testing.zcml')

    def setUpPloneSite(self, portal):
        """ Set up Plone site """
        # Install the example.conference product
        self.applyProfile(portal, 'eea.rdfmarshaller:default')

        if HAS_DEXTERITY:
            self.applyProfile(
                    portal,
                    'eea.rdfmarshaller:dexterity_testfixture')


FIXTURE = Fixture()
INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name='eea.rdfmarshaller:Integration',
)
FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE,),
    name='eea.rdfmarshaller:Functional',
)
