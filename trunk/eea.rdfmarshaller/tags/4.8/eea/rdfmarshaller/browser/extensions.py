"""rdf extensions 
"""

from Products.Five import BrowserView
import logging
#import rdflib
import surf


class RDFExtensions(BrowserView):
    """Publishes rdf extensions
    """

    def __call__(self):
        store = surf.Store(reader='rdflib',  writer='rdflib',
                           rdflib_store = 'IOMemory')
        store.log.setLevel(logging.CRITICAL)
        store.writer.log.setLevel(logging.CRITICAL)
        session = surf.Session(store)

        self.enhance(session)

        data = store.reader.graph.serialize(format='pretty-xml')
        self.request.response.setHeader('Content-Type',
                                        'application/rdf+xml; charset=utf-8')
        return data
        
    def enhance(self, session):
        """Add extensions to the rdf 

        ZZZ: we should add a subscribers mechanism to make it possible to 
        discover additions to the published extensions
        """
        
        #eea:isTranslationOf
        session.rdf_Property = None
