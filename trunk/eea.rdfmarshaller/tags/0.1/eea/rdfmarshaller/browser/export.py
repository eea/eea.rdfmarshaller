from Products.Marshall.registry import getComponent


class RDFExport(object):
    """ """
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        marshaller = getComponent('surfrdf')
        content_type, length, data = marshaller.marshall(self.context)
        self.request.response.setHeader('Content-Type','application/rdf+xml; charset=utf-8')
        return data
