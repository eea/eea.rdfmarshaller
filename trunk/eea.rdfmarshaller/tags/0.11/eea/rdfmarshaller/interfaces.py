from zope.interface import Interface, Attribute
from Products.Archetypes.interfaces import IField

class ISurfSession(Interface):
    """ Marker interface """

class IArchetype2Surf(Interface):
    """ """

class IATField2Surf(Interface):
    """ """

    def value(context):
        """ Returns the value in RDF format """

    exportable = Attribute("Return True if it is possible to export the value to RDF")

        
class IATVocabulary(Interface):
    """ Marker interface for ATVocabularyManager Simple Vocabularym """

class IATVocabularyTerm(Interface):
    """ Marker interface for ATVocabularyManager Simple Term """
    
class IReferenceField(IField):
    """ Marker interface for Products.Archetypes.Field.ReferenceField """

class ITextField(IField):
    """ Marker interface for Products.Archetypes.Field.ReferenceField """
