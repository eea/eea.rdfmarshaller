""" eea.rdfmarshaller package """


from eea.rdfmarshaller import marshaller
from eea.rdfmarshaller import config
from eea.rdfmarshaller.products_marshall_registry import registerComponent

registerComponent('surfrdf', 'RDF Marshaller',
                  marshaller.RDFMarshaller)

registerComponent('surfrdfs', 'RDF Schema Marshaller',
                  marshaller.RDFMarshaller)

__all__ = [config.__name__, ]
