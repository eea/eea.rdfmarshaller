import surf
import rdflib
from OFS.interfaces import IFolder
from zope.interface import implements, Interface
from zope.component import adapts, queryMultiAdapter
from Products.Archetypes.Marshall import Marshaller
from Products.Archetypes.interfaces import IField
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import ITypeInformation
from eea.rdfmarshaller.interfaces import IArchetype2Surf, ISurfSession, IReferenceField
from eea.rdfmarshaller.interfaces import IATVocabularyTerm

class RDFMarshaller(Marshaller):
    """ """

    def demarshall(self, instance, data, **kwargs):
        pass

    def marshall(self, instance, **kwargs):
        store = surf.Store(reader='rdflib',  writer='rdflib', rdflib_store = 'IOMemory')
        session = surf.Session(store)
        content_type = 'text/xml; charset=UTF-8'
        length = data = 0

        atsurf = queryMultiAdapter((instance, session), interface=IArchetype2Surf)
        atsurf.at2surf()
        store.reader.graph.bind(atsurf.prefix, atsurf.namespace, override=False)
        store.reader.graph.bind('dc',surf.ns.DC, override=True)
        data = store.reader.graph.serialize(format = 'pretty-xml')
        return (content_type, length, data)


class ATCTDublinCore2Surf(object):
    implements(IArchetype2Surf)
    adapts(Interface, ISurfSession)
    
    def __init__(self, context, session):
        self.context = context
        self.session = session

class ATField2Surf(object):
    implements(IArchetype2Surf)
    adapts(IField, ISurfSession)

    def __init__(self, context, session):
        self.context = context
        self.session = session

class ATReferenceField2Surf(ATField2Surf):
    implements(IArchetype2Surf)
    adapts(IReferenceField, ISurfSession)

    
class ATCT2Surf(object):
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
                   ])

    field_map = {}

    
    def __init__(self, context, session):
        self.context = context
        self.session = session
        if self.namespace is None:
            ttool = getToolByName(context, 'portal_types')
            surf.ns.register(**{ self.prefix : '%s#' % ttool[context.portal_type].absolute_url()} )
        
    @property
    def blacklist_map(self):
        ptool = getToolByName(self.context,'portal_properties')
        props = getattr(ptool, 'rdfmarshaller_properties', None)
        #TODO: added 'file' to back list as fails with unicode error
        blacklist = ['constrainTypesMode','locallyAllowedTypes', 'immediatelyAddableTypes','language', 'allowDiscussion', 'file'] # fields not to export
        if props:
            blacklist = list(props.getProperty('%s_blacklist' % self.portalType.lower(), props.getProperty('blacklist')))
        return blacklist
    
    @property
    def namespace(self):
        return getattr(surf.ns, self.prefix.upper(), None)
    
    @property
    def prefix(self):
        return self.portalType.lower()

    @property
    def portalType(self):
        return self.context.portal_type.replace(' ','')

    @property
    def surfResource(self):
        try:
            resource = self.session.get_class(self.namespace[self.portalType])(self.subject)
        except:
            #import pdb; pdb.set_trace()
            pass
        resource.bind_namespaces([self.prefix])
        resource.session = self.session
        return resource
    
    @property
    def subject(self):
        return self.context.absolute_url()

    def _schema2surf(self):
        context = self.context
        session = self.session
        resource = self.surfResource
        language = context.Language()
        for field in context.Schema().fields():
            fieldAdapter = queryMultiAdapter((field, self.session), interface=IArchetype2Surf)
            fieldName = field.getName()
            if fieldName in self.blacklist_map:
                continue
            value = field.get(context)
            if value:
                prefix = self.prefix
                if isinstance(value, (list, tuple)):
                    value = list(value)
                    if fieldName == 'relatedItems':
                        value = [ rdflib.URIRef(obj.absolute_url()) for obj in value ]
                else:
                    value = (str(value), language)
                if fieldName in self.field_map:
                    fieldName = self.field_map.get(fieldName)
                elif fieldName in self.dc_map:
                    fieldName = self.dc_map.get(fieldName)
                    prefix = 'dc'
                setattr(resource, '%s_%s' % (prefix, fieldName), value)
        resource.save()
        return resource

    
    def at2surf(self):
        return self._schema2surf()

class ATVocabularyTerm2Surf(ATCT2Surf):
    implements(IArchetype2Surf)
    adapts(IATVocabularyTerm, ISurfSession)

    @property
    def blacklist_map(self):
        return super(ATVocabularyTerm2Surf, self).blacklist_map + ['creation_date', 'modification_date', 'creators']

class ATFolderish2Surf(ATCT2Surf):
    implements(IArchetype2Surf)
    adapts(IFolder, ISurfSession)

    def at2surf(self):
        resource = super(ATFolderish2Surf, self).at2surf()
        for obj in self.context.objectValues():
            atsurf = queryMultiAdapter((obj, self.session), interface=IArchetype2Surf)
            if atsurf is not None:
                self.session.default_store.reader.graph.bind(atsurf.prefix, atsurf.namespace, override=False)
                atsurf.at2surf()

        return resource
        

class ATField2RdfSchema(ATCT2Surf):
    implements(IArchetype2Surf)
    adapts(IField, Interface, ISurfSession)

    def __init__(self, context, fti, session):
        self.context = context
        self.session = session
        self.fti = fti
        
    @property
    def portalType(self):
        return u'Property'

    @property
    def namespace(self):
        return surf.ns.RDFS

    @property
    def prefix(self):
        return 'rdfs'

    @property
    def rdfId(self):
        return self.context.getName().replace(' ','')

    @property
    def subject(self):
        return '%s#%s' % (self.fti.absolute_url(),self.context.getName())

    def _schema2surf(self):
        context = self.context
        session = self.session
        resource = self.surfResource
        
        resource.rdfs_label = (context.widget.label, u'en')
        resource.rdfs_comment = (context.widget.description, u'en')
        resource.rdf_id = self.rdfId
        resource.rdf_domain = rdflib.URIRef(u'#%s' % self.fti.Title())
        resource.save()
        return resource


class FTI2Surf(ATCT2Surf):
    implements(IArchetype2Surf)
    adapts(ITypeInformation, ISurfSession)

    
    blacklist_map = ['constrainTypesMode','locallyAllowedTypes',
                     'immediatelyAddableTypes','language',
                     'creation_date',
                     'modification_date',
                     'creators',
                     'subject',
                     'effectiveDate',
                     'expirationDate',
                     'contributors',
                     'allowDiscussion',
                     'rights'
                     ] # fields not to export, i.e Dublin Core

    @property
    def portalType(self):
        return u'Class'

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
        context = self.context
        session = self.session
        resource = self.surfResource

        attool = getToolByName(context, 'archetype_tool')
        resource.rdfs_label = (context.Title(), u'en')
        resource.rdfs_comment = (context.Description(), u'en')
        resource.rdf_id = self.rdfId
        resource.save()
        schema = attool.lookupType(context.product, context.content_meta_type)['schema']
        for field in schema.fields():
            fieldName = field.getName()
            if fieldName in self.blacklist_map:
                continue

            atsurf = queryMultiAdapter((field, context, session), interface=IArchetype2Surf)
            atsurf.at2surf()
        return resource

    
    def at2surf(self):
        return self._schema2surf()
