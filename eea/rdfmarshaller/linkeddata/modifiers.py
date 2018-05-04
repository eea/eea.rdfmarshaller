import surf
from eea.rdfmarshaller.interfaces import (ILinkedDataHomepage,
                                          ISurfResourceModifier)
from eea.rdfmarshaller.linkeddata.interfaces import ILinkedDataHomepageData
from Products.CMFCore.interfaces import IContentish
from rdflib.term import Literal
from zope.component import adapts, getMultiAdapter
from zope.interface import implements


class CarouselModifier(object):
    """ Adds information about list of news as a carousel
    """
    implements(ISurfResourceModifier)
    adapts(IContentish)

    def __init__(self, context):
        self.context = context

    def run(self, resource, adapter, session, *args, **kwds):
        """ Run """
        context = self.context
        if context.portal_type not in ['Collection', 'Topic']:
            return
        request = self.context.REQUEST
        b_size = request.get('limit_display', 100)
        brains = self.context.queryCatalog(batch=True, b_size=b_size)

        ItemList = session.get_class(surf.ns.SCHEMA['ItemList'])
        Item = session.get_class(surf.ns.SCHEMA['Article'])
        ListElement = session.get_class(surf.ns.SCHEMA['ListItem'])
        ilist = ItemList("#itemList")
        site = get_site(context)
        publisher = ''
        if site:
            ld = ILinkedDataHomepageData(site)
            org_url = site.absolute_url()
            publisher = get_organisation(session, ld, org_url)

        position = 0
        for brain in brains:
            url = brain.getURL()
            position += 1
            list_item = ListElement("ListItem" + str(position))
            list_item.schema_position = position
            item = Item(url)
            # google has a limit of max 110 characters for headline if more
            # you get a validation error
            item.schema_headline = brain.Title if len(brain.Title) <= 110 else \
                brain.Title[0:107] + "..."
            item.schema_url = url
            item.schema_mainEntityOfPage = url
            item.schema_image = Literal(url + '/image_large')
            item.schema_author = brain.Creator
            item.schema_publisher = publisher
            item.schema_datePublished = brain.EffectiveDate
            item.schema_dateModified = brain.ModificationDate
            item.update()
            list_item.schema_item = item
            list_item.update()
            ilist.schema_itemListElement.append(list_item)
        items_len = len(ilist.schema_itemListElement)
        for n, el in enumerate(ilist.schema_itemListElement):
            el.schema_position = Literal(items_len - n)
            el.update()
        ilist.update()


class BreadcrumbModifier(object):
    """ Adds information about breadcrumbs for a page
    """

    implements(ISurfResourceModifier)
    adapts(IContentish)

    def __init__(self, context):
        self.context = context

    def run(self, resource, adapter, session, *args, **kwds):
        """ run """
        parent = self.context
        if ILinkedDataHomepage.providedBy(parent):
            return

        BreadcrumbList = session.get_class(surf.ns.SCHEMA['BreadcrumbList'])
        Item = session.get_class(surf.ns.SCHEMA['Thing'])
        ListElement = session.get_class(surf.ns.SCHEMA['ListItem'])
        blist = BreadcrumbList("#breadcrumb")

        position = 0
        while not ILinkedDataHomepage.providedBy(parent):
            try:
                if position != 0:
                    parent = parent.aq_parent
                url = parent.absolute_url()
                position += 1
                list_item = ListElement("ListItem" + str(position))
                list_item.schema_position = position
                item = Item(url + "#breadcrumb")
                item.schema_name = parent.Title()
                item.schema_image = Literal(url + '/image_large')
                item.schema_url = url
                item.update()
                list_item.schema_item = item
                list_item.update()
                blist.schema_itemListElement.append(list_item)
            except AttributeError:
                break
        items_len = len(blist.schema_itemListElement)
        for n, el in enumerate(blist.schema_itemListElement):
            el.schema_position = Literal(items_len - n)
            el.update()
        blist.update()


def to_literal_list(text):
    """  to_literal_list
    """
    if not text:
        return []

    return [Literal(x.strip())
            for x in text.strip().split('\n')

            if x and x.strip()]


def get_site(context):
    """ retrieve site """
    site = context

    while not ILinkedDataHomepage.providedBy(site):
        try:
            site = site.aq_parent
        except AttributeError:
            site = None
            return site
    return site


def get_organisation(session, homepage, org_url):
    """ retrieve organisation/publisher data """
    ld = homepage
    ContactPoint = session.get_class(surf.ns.SCHEMA['ContactPoint'])
    Organization = session.get_class(surf.ns.SCHEMA['Organization'])
    Image = session.get_class(surf.ns.SCHEMA['ImageObject'])

    org = Organization(org_url + "#organization")
    org.schema_name = ld.name

    logo = Image(ld.logo_url + "#logo")
    logo.schema_url = ld.logo_url

    if hasattr(ld, 'logo_width'):
        logo.schema_width = Literal(str(ld.logo_width) + 'px')
        logo.schema_height = Literal(str(ld.logo_height) + 'px')

    if hasattr(ld, 'social_profile_links'):
        social_links = to_literal_list(ld.social_profile_links)
        org.schema_sameAs = social_links

    contact_points = getattr(ld, 'contact_points', [])

    for index, info in enumerate(contact_points):
        tel = info['telephone']
        contactType = info['contactType']

        langs = to_literal_list(info.get('availableLanguage', ''))
        contactOption = info.get('contactOption')

        cp = ContactPoint("{0}#contact-point-{1}".format(org_url, index))
        cp.schema_telephone = tel
        cp.schema_contactType = contactType

        if langs:
            cp.schema_availableLanguage = langs

        if contactOption:
            cp.schema_contactOption = contactOption

        cp.update()
        org.schema_contactPoint.append(cp)

    org.schema_logo = logo

    logo.update()
    org.update()
    return org


class OrganizationModifier(object):
    """ Adds info about publishing organisation based on ILinkedDataHomepage
    """

    implements(ISurfResourceModifier)
    adapts(IContentish)

    def __init__(self, context):
        self.context = context

    def run(self, resource, adapter, session, *args, **kwds):
        """ Run """
        site = get_site(self.context)
        if not site:
            return
        org_url = site.absolute_url()
        ld = ILinkedDataHomepageData(site)

        if not getattr(ld, 'name', None):     # LD information is not there
            return
        org = get_organisation(session, ld, org_url)

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
        WebSite = session.get_class(surf.ns.SCHEMA['WebSite'])
        website = WebSite(url + "#website")
        website.schema_url = url

        ld = ILinkedDataHomepageData(self.context)

        if getattr(ld, 'search_action_url', None):
            action = SearchAction()
            target = self.context.absolute_url() + ld.search_action_url
            action.schema_target = Literal(target)

            qi_uri = surf.ns.SCHEMA['query-input']
            action.update()
            graph = action.graph()
            qi = (action.subject,
                  qi_uri,
                  Literal("required name=search_term_string"))
            graph.add(qi)

            action.set(graph)
            action.update()
            website.schema_potentialAction = action

        website.update()


class DefaultPageModifier(object):
    """ Detects if context is used as default page for a LinkedData homepage
    """

    implements(ISurfResourceModifier)
    adapts(IContentish)

    def __init__(self, context):
        self.context = context

    def run(self, resource, adapter, session, *args, **kwds):
        """ Add LinkedDataHomepage information to rdf """

        view = getMultiAdapter((self.context, self.context.REQUEST),
                               name="plone_context_state")

        if view.is_view_template():
            root = view.canonical_object()

            if ILinkedDataHomepage.providedBy(root):
                modifier = HomepageModifier(root)
                modifier.run(resource, adapter, session, *args, **kwds)
