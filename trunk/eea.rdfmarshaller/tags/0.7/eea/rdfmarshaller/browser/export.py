from Products.Marshall.registry import getComponent


class RDFExport(object):
    """ """
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        marshaller = getComponent('surfrdf')
        endLevel = int(self.request.get('endLevel',1))
        content_type, length, data = marshaller.marshall(self.context, endLevel=endLevel)
        self.request.response.setHeader('Content-Type','application/rdf+xml; charset=utf-8')
        return data

class RDFSExport(object):
    """ """
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        marshaller = getComponent('surfrdfs')
        content_type, length, data = marshaller.marshall(self.context)
        self.request.response.setHeader('Content-Type','application/rdf+xml; charset=utf-8')
        return data
