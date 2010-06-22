import surf
import rdflib
from zope.interface import implements, Interface
from zope.component import adapts, queryMultiAdapter
from Products.Archetypes.Marshall import Marshaller
from eea.rdfmarshaller.interfaces import IArchetype2Surf, ISurfSession

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
    
class ATCT2Surf(object):
    implements(IArchetype2Surf)
    adapts(Interface, ISurfSession)
    
    dc_map = dict([('title', 'Title'),
                   ('description', 'Description'),
                   ('creation_date', 'created'),
                   ('modification_date', 'modified'),
                   ('creators', 'Creator'),
                   ('subject', 'Subject'),
                   ('effectiveDate', 'effective'),
                   ('expirationDate', 'expires'),
                   ])

    field_map = {}
    blacklist_map = ['constrainTypesMode','locallyAllowedTypes', 'immediatelyAddableTypes'] # fields not to export
    
    def __init__(self, context, session):
        self.context = context
        self.session = session
        
    @property
    def namespace(self):
        return surf.ns.ATCT

    @property
    def prefix(self):
        return 'atct'

    @property
    def portalType(self):
        return self.context.portal_type.replace(' ','')

    @property
    def surfResource(self):
        resource = self.session.get_class(self.namespace[self.portalType])(self.subject)
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
        
        for field in context.Schema().fields():
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
                    value = str(value)
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
