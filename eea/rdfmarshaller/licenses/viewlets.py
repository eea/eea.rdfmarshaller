import StringIO

import surf
from eea.rdfmarshaller.licenses.license import ILicenses, IPortalTypeLicenses
from plone import api
from plone.app.layout.viewlets.common import ViewletBase
from plone.memoize.ram import cache
from Products.Marshall.registry import getComponent
from rdflib import ConjunctiveGraph  # , Graph


has_license_query = """
PREFIX odsr: <http://schema.theodi.org/odrs#>

ASK { ?s odsr:contentLicense ?o }
"""

license_query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX odsr: <http://schema.theodi.org/odrs#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX dcat: <http://www.w3.org/ns/dcat#>

CONSTRUCT {
    ?s ?p ?o .

    ?sa dct:rights ?rights .
    ?sa dct:title ?title .
    ?sa rdf:type dcat:Dataset .

    ?sa dct:license ?lic .
}
WHERE {
    {
        GRAPH ?a {
            ?s odsr:contentLicense ?v
        } .
        GRAPH ?a {
            ?s ?p ?o
        }
    } .
    {
        ?sa dct:rights ?rights .
        ?sa dct:title ?title .
        ?sa dct:license ?lic .
        # ?lic dct:title ?lictitle .
    }
}
"""         # % URL


def json_serialize(res):
    s = surf.Store(reader='rdflib', writer='rdflib', rdflib_store='IOMemory')

    for triple in res:
        s.add_triple(*triple)

    context = {
        "odrs": "http://schema.theodi.org/odrs#",
        "dct": "http://purl.org/dc/terms/",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "dcat": "http://www.w3.org/ns/dcat#",
    }

    ser = s.reader.graph.serialize(format='json-ld', context=context)

    return ser


def regraph(store):
    """ Change the content of store to a ConjunctiveGraph.

    ConjunctiveGraphs allow queries to look at a graph instead of separate
    triples.
    """

    ser = store.reader.graph.serialize(format='xml')
    f = StringIO.StringIO(ser)
    graph = ConjunctiveGraph()
    graph.parse(f)

    return graph


def license_key(method, view):
    context = view.context
    path = '/'.join(context.getPhysicalPath())
    modified = getattr(context, 'modified', lambda: '')()

    key = "{0}-{1}".format(path, modified)

    return key


class LicenseViewlet(ViewletBase):
    """ json-ld license content
    """

    def available(self):
        try:
            reg_types = api.portal.get_registry_record(
                'rdfmarshaller_type_licenses', interface=IPortalTypeLicenses
            )
        except KeyError:
            return None

        try:
            reg_licenses = api.portal.get_registry_record(
                'rdfmarshaller_licenses', interface=ILicenses)
        except KeyError:
            return None

        if not (reg_types and reg_licenses):
            return

        return True

    @cache(license_key)
    def render(self):
        if not self.available():
            return ''

        marshaller = getComponent('surfrdf')
        ser = marshaller.marshall(self.context, endLevel=1)

        if not ser:
            return ""

        store = marshaller.store

        graph = regraph(store)
        has_license = list(graph.query(has_license_query))

        if False in has_license:
            return ""

        res = graph.query(license_query)
        json = json_serialize(res)

        if json is None:
            return ""

        return '<script type="application/ld+json">%s</script>' % json
