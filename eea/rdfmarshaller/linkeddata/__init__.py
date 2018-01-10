import rdflib
import surf
from eea.rdfmarshaller.interfaces import ILinkedData, ILinkedDataHomepage
from eea.rdfmarshaller.linkeddata.interfaces import ILinkedDataHomepageData
from persistent import Persistent
from plone.api import portal
from Products.CMFCore.interfaces import IContentish
from zope.annotation.factory import factory
from zope.component import adapts
from zope.interface import implements


def schematize(store):
    graph = store.reader.graph
    triples = list(graph)

    # from pprint import pprint
    # pprint(triples)

    res = [(s, p, v)
           for (s, p, v) in triples

           if (
               v.startswith('http://schema.org') or
               p.startswith('http://schema.org')
           )]
    s = surf.Store(reader='rdflib', writer='rdflib', rdflib_store='IOMemory')

    for triple in res:
        s.add_triple(*triple)

    return s


portal_types_map = {
    'Document': 'Article',
}


class GenericLinkedData(object):
    """ Generic ILinkedData implemention """

    implements(ILinkedData)
    adapts(IContentish)

    def __init__(self, context):
        self.context = context

    def get_jsonld_context(self):

        context = {
            surf.ns.SCHEMA['Image']: surf.ns.SCHEMA['ImageObject'],
            surf.ns.SCHEMA['productID']: surf.ns.SCHEMA['about'],
        }

        return context

    def get_site(self):
        site = portal.get()
        ldsite = self.context

        while not ILinkedDataHomepage.providedBy(ldsite):
            try:
                ldsite = ldsite.aq_parent
            except AttributeError:
                ldsite = None

                break

        if ldsite is None:
            return site

        return ldsite

    def modify(self, obj2surf):
        resource = obj2surf.resource
        session = resource.session

        site = self.get_site()
        site_url = site.absolute_url()
        base_url = self.context.absolute_url()

        Article = session.get_class(surf.ns.SCHEMA['Article'])
        Person = session.get_class(surf.ns.SCHEMA['Person'])

        resource.rdf_type.append(surf.ns.SCHEMA['WebPage'])

        article = Article(base_url + "#article")
        article.schema_mainEntityOfPage = resource.subject
        article.schema_headline = resource.dcterms_title.first.value
        article.schema_datePublished = str(resource.dcterms_issued.first)
        article.schema_dateModified = str(resource.dcterms_modified.first)

        name = resource.dcterms_creator.first.value
        author = Person(site_url + "#author:" + name)
        author.schema_name = name

        article.schema_author = author
        article.schema_description = resource.dcterms_abstract

        image = resource.foaf_depiction.first
        image.schema_url = str(image.subject)

        article.schema_image = image.subject

        image.update()
        author.update()
        article.update()
        resource.update()

        article.schema_publisher = rdflib.term.URIRef(site_url)
        article.update()

    def serialize(self, obj2surf):
        """ Folder to Surf """

        self.modify(obj2surf)

        store = obj2surf.session.default_store
        store = schematize(store)

        context = self.get_jsonld_context()
        data = store.reader.graph.serialize(format='json-ld', context=context)
        print data

        return data


class HomepageLinkedData(GenericLinkedData):
    """ ILinkedData implemention for homepages """

    adapts(ILinkedDataHomepage)

    def get_jsonld_context(self):

        context = {
            surf.ns.SCHEMA['Image']: surf.ns.SCHEMA['ImageObject'],
            surf.ns.SCHEMA['productID']: surf.ns.SCHEMA['about'],
        }

        return context

    def modify(self, obj2surf):
        pass


class LinkedDataHomepageData(Persistent):

    adapts(ILinkedDataHomepage)
    implements(ILinkedDataHomepageData)


KEY = 'LinkedDataHomepage'

linked_data_annotation = factory(LinkedDataHomepageData, key=KEY)
