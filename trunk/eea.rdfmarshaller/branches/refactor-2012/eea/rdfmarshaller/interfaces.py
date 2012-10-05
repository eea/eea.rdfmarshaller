""" Interfaces """
from zope.interface import Interface, Attribute
from Products.Archetypes.interfaces import IField


class ISurfSession(Interface):
    """The surf.Session objects"""


class IObject2Surf(Interface):
    """ An adapter that writes surf info into a ISurfSession
    """

    def write():
        """Add necessary info into the session
        """


class ISurfResourceModifier(Interface):
    """Plugins that can modify the saved resource for a given context
    """

    def run(resource):
        """Gets the rdf resource as argument, to allow it to change inplace
        """
