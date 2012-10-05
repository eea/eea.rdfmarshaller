""" Interfaces """
from zope.interface import Interface, Attribute
from Products.Archetypes.interfaces import IField

class ISurfSession(Interface):
    """ Marker interface """

class IArchetype2Surf(Interface):
    """ IArchetype2Surf interface """

class IATField2Surf(Interface):
    """ IATField2Surf interface """

    def value(context):
        """ Returns the value in RDF format """

    exportable = Attribute("Return True if it is possible to export the value "
                           "to RDF")


class IATVocabulary(Interface):
    """ Marker interface for ATVocabularyManager Simple Vocabulary """

class IATVocabularyTerm(Interface):
    """ Marker interface for ATVocabularyManager Simple Term """

class IReferenceField(IField):
    """ Marker interface for Products.Archetypes.Field.ReferenceField """

class ITextField(IField):
    """ Marker interface for Products.Archetypes.Field.TextField """


class ISurfResourceModifier(Interface):
    """Plugins that can modify the saved resource for a given context
    """

    def run(resource):
        """Gets the rdf resource as argument, to allow it to change inplace
        """
