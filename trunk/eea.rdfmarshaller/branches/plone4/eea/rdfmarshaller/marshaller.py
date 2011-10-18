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
from eea.rdfmarshaller.interfaces import IATVocabularyTerm
from eea.rdfmarshaller.interfaces import IArchetype2Surf, IATField2Surf
from eea.rdfmarshaller.interfaces import ISurfSession, IReferenceField
from zope.component import adapts, queryMultiAdapter
from zope.interface import implements, Interface
import logging
import rdflib
import surf
import sys

logging.basicConfig(level=logging.CRITICAL)


class RDFMarshaller(Marshaller):
    """ Marshal content types instances into RDF format """

    def demarshall(self, instance, data, **kwargs):
        """ de-marshall """
        pass

    def marshall(self, instance, **kwargs):
        """ marshall """
        store = surf.Store(reader='rdflib',  writer='rdflib',
                           rdflib_store = 'IOMemory')
        store.log.setLevel(logging.CRITICAL)
        store.writer.log.setLevel(logging.CRITICAL)
        session = surf.Session(store)
        content_type = 'text/xml; charset=UTF-8'
        length = data = 0

        atsurf = queryMultiAdapter((instance, session),
                                   interface=IArchetype2Surf)
        endLevel = kwargs.get('endLevel', 1)
        atsurf.at2surf(endLevel=endLevel)
        store.reader.graph.bind(atsurf.prefix,
                                atsurf.namespace,
                                override=False)
        store.reader.graph.bind('dc',
                                surf.ns.DC,
                                override=True)
        store.reader.graph.bind('dcterms',
                                surf.ns.DCTERMS,
                                override=True)
        data = store.reader.graph.serialize(format='pretty-xml')
        return (content_type, length, data)


class ATCTDublinCore2Surf(object):
    """Base implementation of IArchetype2Surf """
    implements(IArchetype2Surf)
    adapts(Interface, ISurfSession)

    def __init__(self, context, session):
        self.context = context
        self.session = session


class ATField2Surf(object):
    """Base implementation of IATField2Surf"""
    implements(IATField2Surf)
    adapts(IField, ISurfSession)

    exportable = True

    def __init__(self, context, session):
        self.field = context
        self.session = session

    def value(self, context):
        """ Value """
        return self.field.getAccessor(context)()


class ATFileField2Surf(ATField2Surf):
    """IATField2Surf implementation for File fields"""
    implements(IATField2Surf)
    adapts(IFileField, ISurfSession)

    exportable = False


class ATReferenceField2Surf(ATField2Surf):
    """IATField2Surf implementation for Reference fields"""
    implements(IATField2Surf)
    adapts(IReferenceField, ISurfSession)

    def value(self, context):
        """ Value """
        value = self.field.getAccessor(context)()
        return [ rdflib.URIRef(obj.absolute_url()) for obj in value ]


class ATCT2Surf(object):
    """IArchetype2Surf implementation for ATCT"""

    implements(IArchetype2Surf)
    adapts(Interface, ISurfSession)

    dc_map = dict([('title', 'title'),
                   ('description', 'description'),
                   ('creation_date', 'created'),
                   ('modification_date', 'modified'),
                   ('creators', 'creator'),
                   ('subject', 'subject'),
                   ('effectiveDate', 'effective'),
                   ('expirationDate', 'expires'),
                   ('rights', 'rights'),
                   ])

    field_map = {}

    def __init__(self, context, session):
        self.context = context
        self.session = session
        if self.namespace is None:
            ttool = getToolByName(context, 'portal_types')
            surf.ns.register(**{ self.prefix : '%s#' %
                                 ttool[context.portal_type].absolute_url()} )

    @property
    def blacklist_map(self):
        """ Blacklist map """
        ptool = getToolByName(self.context,'portal_properties')
        props = getattr(ptool, 'rdfmarshaller_properties', None)
        # fields not to export
        blacklist = ['constrainTypesMode',
                     'locallyAllowedTypes',
                     'immediatelyAddableTypes',
                     'language',
                     'allowDiscussion']
        if props:
            blacklist = list(props.getProperty('%s_blacklist' %
                self.portalType.lower(), props.getProperty('blacklist')))
        return blacklist

    @property
    def namespace(self):
        """ Namespace """
        return getattr(surf.ns, self.prefix.upper(), None)

    @property
    def prefix(self):
        """ Prefix """
        return self.portalType.lower()

    @property
    def portalType(self):
        """ Portal type """
        return self.context.portal_type.replace(' ','')

    @property
    def surfResource(self):
        """ Surf resource """
        try:
            resource = self.session.get_class(
                self.namespace[self.portalType])(self.subject)
        except Exception:
            log.log('RDF marshaller error \n%s: %s' %
                    (sys.exc_info()[0], sys.exc_info()[1]),
                    severity=log.logging.WARN)
            return None

        resource.bind_namespaces([self.prefix])
        resource.session = self.session
        return resource

    @property
    def subject(self):
        """ Subject """
        return self.context.absolute_url()

    def _schema2surf(self):
        """ Schema to Surf """
        context = self.context
        #session = self.session
        resource = self.surfResource
        language = context.Language()

        for field in context.Schema().fields():
            fieldName = field.getName()
            if fieldName in self.blacklist_map:
                continue
            fieldAdapter = queryMultiAdapter((field, self.session),
                    interface=IATField2Surf)

            if fieldAdapter.exportable:
                try:
                    value = fieldAdapter.value(context)
                except TypeError:
                    log.log('RDF marshaller error for context[field]'
                            ' "%s[%s]": \n%s: %s' %
                            (context.absolute_url(), fieldName,
                             sys.exc_info()[0], sys.exc_info()[1]),
                             severity=log.logging.WARN)
                    continue

                if (value and value != "None") or \
                        (isinstance(value, basestring) and value.strip()) :
                    prefix = self.prefix

                    if isinstance(value, (list, tuple)):
                        value = list(value)
                    elif isinstance(value, DateTime):
                        value = (value.HTML4(), None, 'http://www.w3.org/2001/XMLSchema#dateTime')
                    elif isinstance(value, str):
                        value = (value, language)
                    elif isinstance(value, unicode):
                        pass
                    else:
                        try:
                            value = (unicode(value, 'utf-8', 'replace'), language)
                        except TypeError:
                            value = str(value)

                    if fieldName in self.field_map:
                        fieldName = self.field_map.get(fieldName)
                    elif fieldName in self.dc_map:
                        fieldName = self.dc_map.get(fieldName)
                        prefix = 'dcterms'

                    try:
                        setattr(resource, '%s_%s' % (prefix, fieldName), value)
                    except Exception:
                        log.log('RDF marshaller error for context[field]'
                                '"%s[%s]": \n%s: %s' %
                                (context.absolute_url(), fieldName,
                                 sys.exc_info()[0], sys.exc_info()[1]),
                                 severity=log.logging.WARN)

        parent = getattr(aq_inner(context), 'aq_parent', None)
        wftool = getToolByName(context, 'portal_workflow')
        if (parent is not None):
            try:
                state = wftool.getInfoFor(parent, 'review_state')
            except WorkflowException:   #object has no workflow, we assume public, see #4418
                state = 'published'

            if state == 'published':
                resource.dcterms_isPartOf = \
                    rdflib.URIRef(parent.absolute_url()) #pylint: disable-msg = W0612

        resource.save()
        return resource

    def at2surf(self, currentLevel=0, endLevel=1, **kwargs):
        """ AT to Surf """
        return self._schema2surf()


class ATVocabularyTerm2Surf(ATCT2Surf):
    """IArchetype2Surf implemention for ATVocabularyTerms"""
    implements(IArchetype2Surf)
    adapts(IATVocabularyTerm, ISurfSession)

    @property
    def blacklist_map(self):
        """ Blacklist map """
        return super(ATVocabularyTerm2Surf, self).blacklist_map + \
                ['creation_date', 'modification_date', 'creators']


class ATFolderish2Surf(ATCT2Surf):
    """IArchetype2Surf implemention for Folders"""

    implements(IArchetype2Surf)
    adapts(IFolder, ISurfSession)

    def at2surf(self, currentLevel=0, endLevel=1, **kwargs):
        """ AT to Surf """
        currentLevel += 1
        resource = super(ATFolderish2Surf, self).at2surf(
                currentLevel=currentLevel, endLevel=endLevel)
        if currentLevel <= endLevel or endLevel == 0:
            resource.dcterms_hasPart = []

            objs = [b.getObject() for b in self.context.getFolderContents()]
                    #contentFilter={'review_state':'published'})] 
 
            for obj in objs: 
                resource.dcterms_hasPart.append(rdflib.URIRef(
                                                    obj.absolute_url()))
                atsurf = queryMultiAdapter((obj, self.session),
                                            interface=IArchetype2Surf)
                if atsurf is not None:
                    self.session.default_store.reader.graph.bind(
                            atsurf.prefix, atsurf.namespace, override=False)
                    atsurf.at2surf(currentLevel=currentLevel, endLevel=endLevel)
        resource.save()
        return resource


class ATField2RdfSchema(ATCT2Surf):
    """IArchetype2Surf implemention for Fields"""

    implements(IArchetype2Surf)
    adapts(IField, Interface, ISurfSession)

    def __init__(self, context, fti, session):
        super(ATField2RdfSchema, self).__init__(context, session)
        self.fti = fti

    @property
    def portalType(self):
        """ portal type """
        return u'Property'

    @property
    def namespace(self):
        """ namespace """
        return surf.ns.RDFS

    @property
    def prefix(self):
        """ prefix """
        return 'rdfs'

    @property
    def rdfId(self):
        """ rdf id """
        return self.context.getName().replace(' ','')

    @property
    def subject(self):
        """ subject """
        return '%s#%s' % (self.fti.absolute_url(), self.context.getName())

    def _schema2surf(self):
        """ Schema to Surf """
        context = self.context
        resource = self.surfResource

        widget_label = (context.widget.label, u'en')
        widget_description = (context.widget.description, u'en')
        fti_title = rdflib.URIRef(u'#%s' % self.fti.Title())

        setattr(resource, 'rdfs_label', widget_label)
        setattr(resource, 'rdfs_comment', widget_description)
        setattr(resource, 'rdf_id', self.rdfId)
        setattr(resource, 'rdf_domain', fti_title)
        resource.save()
        return resource

class FTI2Surf(ATCT2Surf):
    """ IArchetype2Surf implemention for TypeInformations """
    implements(IArchetype2Surf)
    adapts(ITypeInformation, ISurfSession)

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
                     'rights'
                     ]

    @property
    def portalType(self):
        """ portal type """
        return u'Class'

    @property
    def namespace(self):
        """ namespace """
        return surf.ns.RDFS

    @property
    def prefix(self):
        """ prefix """
        return 'rdfs'

    @property
    def rdfId(self):
        """ rdf id """
        return self.context.getId().replace(' ','')

    @property
    def subject(self):
        """ subject """
        return '%s#%s' % (self.context.absolute_url(), self.rdfId)

    def _schema2surf(self):
        """ Schema to Surf """
        context = self.context
        session = self.session
        resource = self.surfResource

        setattr(resource, 'rdfs_label', (context.Title(), u'en'))
        setattr(resource, 'rdfs_comment', (context.Description(), u'en'))
        setattr(resource, 'rdf_id', self.rdfId)
        resource.save()

        # we need an instance to get full schema with extended fields
        portal_type = context.getId()
        tmpFolder = getToolByName(context, 'portal_url').getPortalObject().\
                portal_factory._getTempFolder(portal_type)
        instance = getattr(tmpFolder, 'rdfstype', None)
        if instance is None:
            try: 
                instance = _createObjectByType(portal_type, tmpFolder,  
                            'rdfstype') 
            except:   #might be a tool class 
                log.log('RDF marshaller error for FTI' 
                        ' "%s": \n%s: %s' %  
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

                atsurf = queryMultiAdapter((field, context, session),
                                           interface=IArchetype2Surf)
                atsurf.at2surf()

        return resource

    def at2surf(self, currentLevel=0, endLevel=1, **kwargs):
        """ AT to Surf """
        return self._schema2surf()

 
class PortalTypesUtil2Surf(ATCT2Surf): 
    """IArchetype2Surf implemention for TypeInformations""" 
    implements(IArchetype2Surf) 
    adapts(ITypesTool, ISurfSession) 
     
    @property 
    def portalType(self): 
        return u'PloneUtility' 
 
    @property 
    def namespace(self): 
        return surf.ns.RDFS 
 
    @property 
    def prefix(self): 
        return 'rdfs' 
 
    @property 
    def rdfId(self): 
        return self.context.getId().replace(' ','') 
 
    @property 
    def subject(self): 
        return '%s#%s' % (self.context.absolute_url(),self.rdfId) 
     
    def _schema2surf(self): 
        #context = self.context 
        #session = self.session 
        resource = self.surfResource 
 
        resource.rdfs_label = (u"Plone PortalTypes Tool", None) 
        resource.rdfs_comment = (u"Holds definitions of portal types", None) 
        resource.rdf_id = self.rdfId 
        resource.save() 
 
    def at2surf(self, **kwargs): 
        return self._schema2surf() 
 
