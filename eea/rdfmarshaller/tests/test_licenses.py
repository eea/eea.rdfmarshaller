""" Test licenses feature """

import unittest

from eea.rdfmarshaller.licenses.license import ILicenses, IPortalTypeLicenses
from eea.rdfmarshaller.testing import INTEGRATION_TESTING
from plone import api
from plone.app.testing import TEST_USER_ID, setRoles
from plone.app.upgrade.utils import loadMigrationProfile


class TestProgramIntegration(unittest.TestCase):
    """ Integration testing """

    layer = INTEGRATION_TESTING

    def setUp(self):
        """ Setup """

        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal.invokeFactory('testpage', 'test-page')
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        self.page = self.portal['test-page']
        self.page.edit(title="Test title", description="Test description")

        loadMigrationProfile(self.portal, 'profile-eea.rdfmarshaller:default')

    def test_licenses(self):
        """ test licenses """

        # TEST @@licenses-settings exists
        licenses_settings = self.portal.unrestrictedTraverse(
            'licenses-settings')
        assert str(type(licenses_settings)) == \
            "<class 'Products.Five.metaclass.LicensesView'>"

        # TEST @@portal-type-licenses-settings exists
        portal_type_licenses_settings = self.portal.unrestrictedTraverse(
            'portal-type-licenses-settings')
        assert str(type(portal_type_licenses_settings)) == \
            "<class 'Products.Five.metaclass.PortalTypeLicensesView'>"

        # TEST registry
        test_licenses = [
            {
                'url': 'http://mit-license.com',
                'text': u'This is MIT license.',
                'id': 'MIT',
                'copyright': 'Copyright 2017',
                'attribution': 'Test Department'
            },
            {
                'url': 'http://cc-license.com',
                'text': u'This is CC license.',
                'id': 'CC',
                'copyright': 'Copyright 2015',
                'attribution': 'Department'
            }
        ]

        # TEST registry: licenses are saved
        api.portal.set_registry_record(
            name='rdfmarshaller_licenses',
            value=test_licenses,
            interface=ILicenses
        )
        reg_licenses = api.portal.get_registry_record(
            'rdfmarshaller_licenses', interface=ILicenses)
        assert reg_licenses == test_licenses

        # TEST registry: licenses-types are saved
        # (Pdb) self.portal['test-page'].portal_type
        # 'testpage' - so, let's use it:
        test_portal_type_licenses = {'testpage': 'CC'}
        api.portal.set_registry_record(
            name='rdfmarshaller_type_licenses',
            value=test_portal_type_licenses,
            interface=IPortalTypeLicenses
        )
        reg_types = api.portal.get_registry_record(
            'rdfmarshaller_type_licenses', interface=IPortalTypeLicenses)
        assert reg_types == test_portal_type_licenses

        # TEST license viewlet rendering
        page = self.portal['test-page']()
        assert '<script type="application/ld+json">' in page
        assert 'http://cc-license.com' in page
        assert 'http://mit-license.com' not in page
        assert 'odrs:copyrightNotice' in page
        assert 'Copyright 2017' not in page
        assert 'Copyright 2015' in page
        assert 'Test Department' not in page
        assert 'Department' in page

        # TEST license viewlet rendering in Plone Site
        page = self.portal()
        assert """<script type="application/ld+json">""" not in page
        assert """http://cc-license.com""" not in page
        assert """http://mit-license.com""" not in page
        assert """odrs:copyrightNotice""" not in page


def test_suite():
    """ test suite """

    return unittest.defaultTestLoader.loadTestsFromName(__name__)
