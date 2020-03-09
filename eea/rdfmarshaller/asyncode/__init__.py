""" Async
"""
from zope.interface import Interface

# BBB Fix this as on python 3.7 even attempting to catch SyntaxError fails
#try:
#    from plone.app.async.interfaces import IAsyncService
#except (ImportError, SyntaxError) as e:
#    class IAsyncService(Interface):
#        """ No async """


class IAsyncService(Interface):
    """ No async """

__all__ = [
    IAsyncService.__name__,
]
