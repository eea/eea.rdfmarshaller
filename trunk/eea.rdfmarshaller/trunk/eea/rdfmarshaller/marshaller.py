import surf
from zope.interface import implements, directlyProvides, Interface
from zope.component import adapts, queryMultiAdapter
from Products.Archetypes.Marshall import Marshaller
from Products.ATContentTypes.interface.interfaces import IATContentType
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
        

    

class ATCT2Surf(object):
    implements(IArchetype2Surf)
    adapts(Interface, ISurfSession)
    
    index_map = dict([('title', 'Title'),
                      ('description', 'Description'),
                      ('creation_date', 'created'),
                      ('modification_date', 'modified'),
                      ('creators', 'Creator'),
                      ('subject', 'Subject'),
                      ('effectiveDate', 'effective'),
                      ('expirationDate', 'expires'),
                      ])
    
    def __init__(self, context, session):
        self.context = context
        self.session = session
        portalType = context.portal_type.replace(' ','')
        surfClass = session.get_class(self.namespace[portalType])
        self.resource = rdfObj = surfClass(context.absolute_url())
        rdfObj.bind_namespaces(['ATCT'])
        rdfObj.session = session

    @property
    def namespace(self):
        return surf.ns.ATCT

    @property
    def prefix(self):
        return 'atct'
    
    def at2surf(self):
        resource = self.resource
        context = self.context
        for field in context.schema.fields():
            value = field.get(context)
            if value:
                if isinstance(value, (list, tuple)):
                    value = list(value)
                else:
                    value = str(value)
                fieldName = self.index_map.get(field.getName(), field.getName())
                prefix = self.prefix
                if fieldName != field.getName():
                    prefix = 'dc'
                setattr(resource, '%s_%s' % (prefix, fieldName), value)
        resource.save()
        return resource
