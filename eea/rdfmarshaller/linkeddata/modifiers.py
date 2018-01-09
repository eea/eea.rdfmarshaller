import surf
from eea.rdfmarshaller.interfaces import (ILinkedDataHomepage,
                                          ISurfResourceModifier)
from eea.rdfmarshaller.linkeddata.interfaces import ILinkedDataHomepageData
from Products.CMFCore.interfaces import IContentish
from rdflib.term import Literal
from zope.component import adapts
from zope.interface import implements

# from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot


class OrganizationModifier(object):
    """ Adds info about publishing organisation based on ILinkedDataHomepage
    """

    implements(ISurfResourceModifier)
    adapts(IContentish)

    def __init__(self, context):
        self.context = context

    def run(self, resource, adapter, session, *args, **kwds):
        """ Add LinkedDataHomepage information to rdf """

        site = self.context

        while not ILinkedDataHomepage.providedBy(site):
            try:
                site = site.aq_parent
            except AttributeError:
                site = None

                return

        ld = ILinkedDataHomepageData(site)

        Organization = session.get_class(surf.ns.SCHEMA['Organization'])
        Image = session.get_class(surf.ns.SCHEMA['ImageObject'])

        org = Organization(site.absolute_url())
        org.schema_name = ld.name

        logo = Image()
        logo.schema_url = ld.logo_url
        logo.update()
        logo.save()

        org.schema_logo = logo
        org.update()
        org.save()

        resource.schema_publisher = org
        resource.update()


class HomepageModifier(object):
    """ Add info about linked data homepage
    """

    implements(ISurfResourceModifier)
    adapts(ILinkedDataHomepage)

    def __init__(self, context):
        self.context = context

    def run(self, resource, adapter, session, *args, **kwds):
        """ Add LinkedDataHomepage information to rdf """

        SearchAction = session.get_class(surf.ns.SCHEMA['SearchAction'])

        url = self.context.absolute_url()
        # we change the rdf type of the plone site. The problem is that we
        # can't have multiple resources with the same subject in the schema,
        # so instantiating a Website(self.context.absolute_url()) will yield
        # unpredictable results

        resource.rdf_type = surf.ns.SCHEMA['WebSite']
        resource.schema_url = url

        ld = ILinkedDataHomepageData(self.context)

        if ld.search_action_url:
            action = SearchAction()
            action.schema_target = Literal(ld.search_action_url)

            qi_uri = surf.ns.SCHEMA['query-input']
            action.update()
            graph = action.graph()
            qi = (action.subject,
                  qi_uri,
                  Literal("required name=search_term_string"))
            graph.add(qi)

            action.set(graph)
            action.update()
            resource.schema_potentialAction = action

        resource.update()
