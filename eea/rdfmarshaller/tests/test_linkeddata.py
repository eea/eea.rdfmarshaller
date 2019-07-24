""" Test linked data feature """

import unittest
from eea.rdfmarshaller.interfaces import ILinkedDataHomepage

from eea.rdfmarshaller.testing import INTEGRATION_TESTING
from zope.interface import alsoProvides

from plone.app.testing import TEST_USER_ID, setRoles
from plone.app.upgrade.utils import loadMigrationProfile


class TestLinkedDataIntegration(unittest.TestCase):
    """ Integration testing """

    layer = INTEGRATION_TESTING

    def setUp(self):
        """ Setup """

        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        alsoProvides(self.portal, ILinkedDataHomepage)
        self.portal.invokeFactory('testpage', 'test-page')
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        self.page = self.portal['test-page']
        self.page.edit(title="Test title", description="Test description")

        # Cheat condition @@plone_context_state/is_view_template
        self.page.REQUEST['ACTUAL_URL'] = self.page.absolute_url()

        loadMigrationProfile(self.portal, 'profile-eea.rdfmarshaller:default')

    def test_linkeddata_viewlet(self):
        """ test linkeddata modifiers """

        # TEST linkeddata viewlet rendering

        page = self.portal['test-page']()
        assert """<script data-diazo-keep='true' type="application/ld+json">"""\
               in page

    def test_linkeddata_breadcrumb(self):
        """ Markup render for breadcrumb
             {
                  "@id": "http://nohost/plone#breadcrumb",
                  "@type": "http://schema.org/Thing",
                  "http://schema.org/image": "http://nohost/plone/image_large",
                  "http://schema.org/name": "Plone site",
                  "http://schema.org/url": "http://nohost/plone"
                },
                {
                  "@id": "BreadCrumbsListItem2",
                  "@type": "http://schema.org/ListItem",
                  "http://schema.org/item": {
                    "@id": "http://nohost/plone#breadcrumb"
                  },
                  "http://schema.org/position": 1
                },
                {
                  "@id": "BreadCrumbsListItem1",
                  "@type": "http://schema.org/ListItem",
                  "http://schema.org/item": {
                    "@id": "http://nohost/plone/test-page#breadcrumb"
                  },
                  "http://schema.org/position": 2
            }
        """

        # TEST linkeddata breacrumb in viewlet rendering
        page = self.portal['test-page']()

        assert 'BreadCrumbsListItem2' in page
        assert 'http://nohost/plone/test-page#breadcrumb' in page
        assert 'BreadCrumbsListItem1' in page
        assert 'http://nohost/plone#breadcrumb' in page

    def test_linkeddata_carousel(self):
        """ Carousel json-ld export example
            {
              "@id": "#itemList",
              "@type": "http://schema.org/ItemList",
              "http://schema.org/itemListElement": [
                {
                  "@id": "CarouselListItem3"
                },
              ]
            },
            {
              "@id": "CarouselListItem1",
              "@type": "http://schema.org/ListItem",
              "http://schema.org/position": 1,
              "http://schema.org/url": "http://nohost/plone/newsitem1"
            },
        """
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        query = [{
            'i': 'portal_type',
            'o': 'plone.app.querystring.operation.string.is',
            'v': 'News Item',
        }]
        portal = self.portal
        portal.invokeFactory("Collection",
                             "collection",
                             title="New Collection",
                             query=query,
                             sort_on='created',
                             )

        # News Item 1
        portal.invokeFactory(id='newsitem1',
                             type_name='News Item')
        # News Item 1
        portal.invokeFactory(id='newsitem2',
                             type_name='News Item')
        # News Item 1
        portal.invokeFactory(id='newsitem3',
                             type_name='News Item')

        collection = portal['collection']
        results = collection.results(batch=False)

        # Cheat condition @@plone_context_state/is_view_template
        collection.REQUEST['ACTUAL_URL'] = collection.absolute_url()
        view = collection()
        ritem0 = results[0]
        assert ritem0.absolute_url() in view
        ritem1 = results[1]
        assert 'CarouselListItem1' in view
        assert ritem1.absolute_url() in view
        assert 'CarouselListItem2' in view
        ritem2 = results[2]
        assert ritem2.absolute_url() in view
        assert 'CarouselListItem3' in view


def test_suite():
    """ test suite """

    return unittest.defaultTestLoader.loadTestsFromName(__name__)
