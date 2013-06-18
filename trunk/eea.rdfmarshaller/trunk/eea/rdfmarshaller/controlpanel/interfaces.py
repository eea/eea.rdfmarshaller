""" RDF Marshaller Settings interfaces
"""

from zope import schema
from zope.interface import Interface

class IRDFMarshallerSettings(Interface):
    """ RDF Marshaller settings schema
    """
    services_to_ping = schema.List(title=u"Services to ping",
                        description=u'List of CR/SDS services to be pinged '
                                    'when object is created or modified',
                        required=False,
                        default=[],
                        value_type=schema.TextLine(title=u"Service to ping"),
                        )