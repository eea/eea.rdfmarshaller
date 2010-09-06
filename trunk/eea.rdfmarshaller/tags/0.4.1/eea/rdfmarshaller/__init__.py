

from Products.Marshall.registry import registerComponent
from eea.rdfmarshaller import marshaller
import eea.rdfmarshaller.config

registerComponent('surfrdf', 'RDF Marshaller',
                  marshaller.RDFMarshaller)

registerComponent('surfrdfs', 'RDF Schema Marshaller',
                  marshaller.RDFMarshaller)
