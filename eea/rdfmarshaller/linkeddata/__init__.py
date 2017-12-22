import surf
from eea.rdfmarshaller.interfaces import ILinkedData
from Products.CMFCore.interfaces import IContentish
from zope.component import adapts
from zope.interface import implements


def fix_triples(triples):
    for s, p, v in triples:
        print s, p, v
        print "--------"

    return triples


def schematize(store):
    graph = store.reader.graph
    triples = list(graph)
    # triples = fix_triples(triples)
    from pprint import pprint
    pprint(triples)

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

    def modify(self, obj2surf):
        resource = obj2surf.resource
        session = resource.session

        schema_type = portal_types_map.get(self.context.portal_type, 'Article')
        resource.rdf_type.append(surf.ns.SCHEMA[schema_type])

        WebPage = session.get_class(surf.ns.SCHEMA['WebPage'])
        Person = session.get_class(surf.ns.SCHEMA['Person'])

        page = WebPage(self.context.absolute_url())

        resource.schema_mainEntityOfPage = page
        resource.schema_headline = resource.dcterms_title.first.value
        resource.schema_datePublished = str(resource.dcterms_issued.first)
        resource.schema_dateModified = str(resource.dcterms_modified.first)

        author = Person()
        author.schema_name = resource.dcterms_creator.first.value

        resource.schema_author = author
        author.update()
        author.save()

        resource.schema_description = resource.dcterms_abstract

        resource.update()
        resource.save()

    def serialize(self, obj2surf):
        """ Folder to Surf """

        self.modify(obj2surf)

        store = obj2surf.session.default_store
        store = schematize(store)
        S = surf.ns.SCHEMA

        context = {
            S['Image']: S['ImageObject']
        }

        data = store.reader.graph.serialize(format='json-ld', context=context)
        print data

        return data
