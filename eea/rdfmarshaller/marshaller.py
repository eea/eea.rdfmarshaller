""" Marshaller module """

import logging

import surf
from eea.rdfmarshaller.interfaces import (IGenericObject2Surf, IObject2Surf,
                                          ISurfResourceModifier, ISurfSession)
from Products.Archetypes.Marshall import Marshaller
from Products.CMFCore.interfaces._tools import ITypesTool
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from surf.log import set_logger
from zope.component import adapts, queryMultiAdapter, subscribers
from zope.interface import Interface, implements

surf.ns.register(EEA="http://www.eea.europa.eu/ontologies.rdf#")
surf.ns.register(SKOS="http://www.w3.org/2004/02/skos/core#")
surf.ns.register(DCAT="http://www.w3.org/ns/dcat#")
surf.ns.register(SCHEMA="http://schema.org/")
surf.ns.register(ODRS="http://schema.theodi.org/odrs#")

# re-register the RDF + RDFS namespace because in new surf they are closed
# namespaces and they won't "take" the custom terms that we access on them
surf.ns.register(RDF="http://www.w3.org/1999/02/22-rdf-syntax-ns#")
surf.ns.register(RDFS="http://www.w3.org/2000/01/rdf-schema#")

logger = logging.getLogger('eea.rdfmarshaller')
logger.setLevel(level=logging.CRITICAL)
set_logger(logger)

DEBUG = False


class RDFMarshaller(Marshaller):
    """ RDF Marshaller, used as a component by Products.Marshaller

    Marshals content types instances into RDF format """

    _store = None

    def demarshall(self, instance, data, **kwargs):
        """ de-marshall """
        pass    # Should raise NotImplementedError

    @property
    def store(self):
        """Factory for store objects
        """

        if self._store is not None:
            return self._store

        store = surf.Store(reader='rdflib', writer='rdflib',
                           rdflib_store='IOMemory')

        store.reader.graph.bind('dc', surf.ns.DC, override=True)
        store.reader.graph.bind('dcterms', surf.ns.DCTERMS, override=True)
        store.reader.graph.bind('eea', surf.ns.EEA, override=True)
        store.reader.graph.bind('skos', surf.ns.SKOS, override=True)
        store.reader.graph.bind('geo', surf.ns.GEO, override=True)
        store.reader.graph.bind('owl', surf.ns.OWL, override=True)
        store.reader.graph.bind('dcat', surf.ns.DCAT, override=True)
        store.reader.graph.bind('schema', surf.ns.SCHEMA, override=True)
        store.reader.graph.bind('foaf', surf.ns.FOAF, override=True)
        store.reader.graph.bind('odrs', surf.ns.ODRS, override=True)

        self._store = store

        return store

    def _add_content(self, instance, **kwargs):
        session = surf.Session(self.store)

        obj2surf = queryMultiAdapter(
            (instance, session), interface=IObject2Surf
        )

        if obj2surf is None:
            return

        self.store.reader.graph.bind(
            obj2surf.prefix, obj2surf.namespace, override=False
        )
        endLevel = kwargs.get('endLevel', 1)
        obj2surf.write(endLevel=endLevel)

        return obj2surf

    def marshall(self, instance, **kwargs):
        """ Marshall the rdf data to xml representation """

        self._add_content(instance, **kwargs)

        data = self.store.reader.graph.serialize(format='pretty-xml')

        content_type = 'text/xml; charset=UTF-8'

        return (content_type, len(data), data)


class GenericObject2Surf(object):
    """Generic implementation of IObject2Surf

    This is meant to be subclassed and not used directly.
    """

    implements(IGenericObject2Surf)
    adapts(Interface, ISurfSession)

    _resource = None    # stores the surf resource
    _namespace = None   # stores the namespace for this resource
    _prefix = None

    def __init__(self, context, session):
        self.context = context
        self.session = session

    @property
    def prefix(self):
        """ prefix """

        if self._prefix is None:
            raise NotImplementedError

        return self._prefix

    @property
    def portalType(self):
        """ portal type """

        return self.context.__class__.__name__

    @property
    def namespace(self):
        """ namespace """

        if self._namespace is not None:
            return self._namespace

        ttool = getToolByName(self.context, 'portal_types')
        ptype = self.context.portal_type
        ns = {
            self.prefix: '%s#' % ttool[ptype].absolute_url()
        }
        surf.ns.register(**ns)
        self._namespace = getattr(surf.ns, self.prefix.upper())

        return self._namespace

    @property
    def subject(self):
        """ subject; will be inserted as rdf:about """

        return '%s#%s' % (self.context.absolute_url(), self.rdfId)

    @property
    def rdfId(self):
        """ rdf id; will be inserted as rdf:id  """

        return self.context.getId().replace(' ', '')

    @property
    def resource(self, **kwds):
        """ Factory for a new Surf resource """

        if self._resource is not None:
            return self._resource

        try:    # pull a new resource from the surf session
            resource = self.session.get_class(
                self.namespace[self.portalType])(self.subject)
        except Exception:
            if DEBUG:
                raise
            logger.exception('RDF marshaller error:')

            return None

        resource.bind_namespaces([self.prefix])
        resource.session = self.session
        self._resource = resource

        return resource

    def modify_resource(self, resource, *args, **kwds):
        """We allow modification of resource here """

        return resource

    def write(self, *args, **kwds):
        """Write its resource into the session """

        if self.resource is None:
            raise ValueError

        # we modify the resource and then allow subscriber plugins to modify it
        resource = self.modify_resource(self.resource, *args, **kwds)

        for modifier in subscribers([self.context], ISurfResourceModifier):
            modifier.run(resource, self, self.session, *args, **kwds)

        resource.update()
        resource.save()

        return resource


class PortalTypesUtil2Surf(GenericObject2Surf):
    """IObject2Surf implemention for TypeInformations"""

    adapts(ITypesTool, ISurfSession)

    _prefix = "rdfs"
    _namespace = surf.ns.RDFS

    @property
    def portalType(self):
        """portal type"""

        return u'PloneUtility'

    def modify_resource(self, resource, *args, **kwds):
        """_schema2surf"""

        resource.rdfs_label = (u"Plone PortalTypes Tool", None)
        resource.rdfs_comment = (u"Holds definitions of portal types", None)
        resource.rdf_id = self.rdfId

        return resource


class PloneSite2Surf(GenericObject2Surf):
    """
    """
    adapts(IPloneSiteRoot, ISurfSession)

    @property
    def portalType(self):
        """ Portal type """

        return self.context.portal_type.replace(' ', '')

    @property
    def prefix(self):
        """ Prefix """

        return self.portalType.lower()

    @property
    def subject(self):
        """ Subject """

        return self.context.absolute_url()
