""" Marshaller module """

from Acquisition import aq_inner
from DateTime.DateTime import DateTime
from OFS.interfaces import IFolder
from Products.Archetypes.Marshall import Marshaller
from Products.Archetypes.interfaces import IField, IFileField
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.interfaces import ITypeInformation
from Products.CMFCore.interfaces._tools import ITypesTool
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import log
from Products.CMFPlone.utils import _createObjectByType
from Products.MimetypesRegistry.interfaces import IMimetypesRegistry
from chardet import detect
from eea.rdfmarshaller.interfaces import IATVocabularyTerm
from eea.rdfmarshaller.interfaces import IArchetype2Surf, IATField2Surf
from eea.rdfmarshaller.interfaces import ISurfResourceModifier
from eea.rdfmarshaller.interfaces import ISurfSession, IReferenceField
from zope.component import adapts, queryMultiAdapter, subscribers
from zope.interface import implements, Interface
import logging
import rdflib
import surf
import sys

DEBUG = False

logging.basicConfig(level=logging.CRITICAL)

surf.ns.register(EEA="http://www.eea.europa.eu/ontologies.rdf#")


class RDFMarshaller(Marshaller):
    """ RDF Marshaller, used as a component by Products.Marshaller 
    
    Marshals content types instances into RDF format """

    _store = None

    def demarshall(self, instance, data, **kwargs):
        """ de-marshall """
        pass    #Should raise NotImplementedError

    @property
    def store(self):
        """Factory for store objects
        """
        if self._store is not None:
            return self._store

        store = surf.Store(reader='rdflib',  writer='rdflib',
                           rdflib_store = 'IOMemory')
        store.log.setLevel(logging.CRITICAL)
        store.writer.log.setLevel(logging.CRITICAL)
        store.reader.graph.bind(atsurf.prefix,
                                atsurf.namespace,
                                override=False)
        store.reader.graph.bind('dc',
                                surf.ns.DC,
                                override=True)
        store.reader.graph.bind('dcterms',
                                surf.ns.DCTERMS,
                                override=True)
        store.reader.graph.bind('eea',
                                surf.ns.EEA,
                                override=True)
        store.reader.graph.bind('geo',
                                surf.ns.GEO,
                                override=True)

        self._store = store
        return store

    def marshall(self, instance, **kwargs):
        """ Marshall the rdf data to xml representation """

        session = surf.Session(self.store)
        content_type = 'text/xml; charset=UTF-8'
        length = data = 0   #is this line required? should be len(data)

        obj2surf = queryMultiAdapter((instance, session),
                                      interface=IArchetype2Surf)
        endLevel = kwargs.get('endLevel', 1)
        obj2surf.write(endLevel=endLevel)

        data = self.store.reader.graph.serialize(format='pretty-xml')
        return (content_type, length, data)


class Object2Surf(object):
    """Generic implementation of IObject2Surf

    This is meant to be subclassed and not used directly.
    """

    implements(IObject2Surf)
    adapts(Interface, ISurfSession)

    _resource = None    #stores the surf resource
    _namespace = None   #stores the namespace for this resource
    _prefix = None

    def __init__(self, context, session):
        self.context = context
        self.session = session

    @property
    def prefix(self):
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

        ttool = getToolByName(context, 'portal_types')
        surf.ns.register(**{ self.prefix : '%s#' %
                             ttool[context.portal_type].absolute_url()} )
        self._namespace = getattr(surf.ns, self.prefix)
        return self._namespace

    @property
    def subject(self):
        """ subject; will be inserted as rdf:about """
        return '%s#%s' % (self.context.absolute_url(), self.rdfId)

    @property
    def rdfId(self):
        """ rdf id; will be inserted as rdf:id  """
        return self.context.getId().replace(' ','')

    @property
    def resource(self, **kwds):
        """ Factory for a new Surf resource """

        if self._resource is not None:
            return self._resource

        try:    #pull a new resource from the surf session
            resource = self.session.get_class(
                self.namespace[self.portalType])(self.subject)
        except Exception:
            if DEBUG:
                raise
            log.log('RDF marshaller error \n%s: %s' %
                    (sys.exc_info()[0], sys.exc_info()[1]),
                    severity=log.logging.WARN)
            return None

        resource.bind_namespaces([self.prefix])
        resource.session = self.session
        self._resource = resource
        return resource

    def write(self, **kwds):
        """Write its resource into the session
        """

        resource = self.resource

        #we modify the resource and then allow subscriber plugins to modify it
        resource = self.update_resource()
        for modifier in subscribers([self.context], ISurfResourceModifier):
            modifier.run(resource, **kwds)

        resource.save()


class PortalTypesUtil2Surf(Object2Surf):
    """IArchetype2Surf implemention for TypeInformations"""

    adapts(ITypesTool, ISurfSession)

    _prefix = "rdfs"
    _namespace = surf.ns.RDFS

    @property
    def portalType(self):
        """portal type"""
        return u'PloneUtility'

    def update_resource(self):
        """_schema2surf"""
        resource = self.surfResource

        resource.rdfs_label = (u"Plone PortalTypes Tool", None)
        resource.rdfs_comment = (u"Holds definitions of portal types", None)
        resource.rdf_id = self.rdfId

        return resource


class MimetypesRegistry2Surf(Object2Surf):
    """IArchetype2Surf implementation for mimetypes_registry
    """

    adapts(IMimetypesRegistry, ISurfSession)

    _prefix = "rdfs"
    _namespace = surf.ns.RDFS
    
    @property
    def portalType(self):
        """portalType"""

        return u'PloneUtility'

    def update_resource(self):
        """_schema2surf"""

        resource = self.resource

        resource.rdfs_label = (u"Plone Mimetypes Registry Tool", None)
        resource.rdfs_comment = (u"Holds definitions of mimetypes", None)
        resource.rdf_id = self.rdfId

        mimes = self.context.list_mimetypes()
        resource.rdfs_mimetype = [(i, None) for i in mimes]

        return resource


class FTI2Surf(Object2Surf):
    """ IArchetype2Surf implemention for TypeInformations """

    adapts(ITypeInformation, ISurfSession)

    _namespace = surf.ns.RDFS
    _prefix = 'rdfs'

    # fields not to export, i.e Dublin Core
    blacklist_map = ['constrainTypesMode',
                     'locallyAllowedTypes',
                     'immediatelyAddableTypes',
                     'language',
                     'creation_date',
                     'modification_date',
                     'creators',
                     'subject',
                     'effectiveDate',
                     'expirationDate',
                     'contributors',
                     'allowDiscussion',
                     'rights',
                     'nextPreviousEnabled',
                     'excludeFromNav',
                     'creator'
                     ]

    def update_resource(self):
        """ Schema to Surf """

        context = self.context
        session = self.session
        resource = self.resource

        setattr(resource, 'rdfs_label', (context.Title(), u'en'))
        setattr(resource, 'rdfs_comment', (context.Description(), u'en'))
        setattr(resource, 'rdf_id', self.rdfId)
        resource.update()

        # the following hack creates a new instance of a content to 
        # allow extracting the full schema, with extended fields
        # Is this the only way to do this?
        portal_type = context.getId()
        tmpFolder = getToolByName(context, 'portal_url').getPortalObject().\
                portal_factory._getTempFolder(portal_type)
        instance = getattr(tmpFolder, 'rdfstype', None)

        if instance is None:
            try:
                instance = _createObjectByType(portal_type, tmpFolder,
                            'rdfstype')
                instance.unindexObject()
            except Exception:   #might be a tool class
                if DEBUG:
                    raise
                log.log('RDF marshaller error for FTI "%s": \n%s: %s' %
                        (context.absolute_url(),
                         sys.exc_info()[0], sys.exc_info()[1]),
                         severity=log.logging.WARN)

                return

        if hasattr(instance, 'Schema'):
            schema = instance.Schema()
            for field in schema.fields():
                fieldName = field.getName()
                if fieldName in self.blacklist_map:
                    continue

                field_surf = queryMultiAdapter((field, context, session),
                                              interface=IObject2Surf)
                field_surf.write()

        return resource

