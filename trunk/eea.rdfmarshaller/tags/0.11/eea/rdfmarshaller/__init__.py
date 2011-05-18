from Products.Marshall.registry import registerComponent
from eea.rdfmarshaller import marshaller
from  eea.rdfmarshaller import config

config  #gets rid of pyflakes warning

registerComponent('surfrdf', 'RDF Marshaller',
        marshaller.RDFMarshaller)

registerComponent('surfrdfs', 'RDF Schema Marshaller',
        marshaller.RDFMarshaller)

