from zope.interface import Interface
from Products.Archetypes.interfaces import IField

class ISurfSession(Interface):
    """ Marker interface """

class IArchetype2Surf(Interface):
    """ """

class IATVocabulary(Interface):
    """ Marker interface for ATVocabularyManager Simple Vocabularym """

class IATVocabularyTerm(Interface):
    """ Marker interface for ATVocabularyManager Simple Term """
    
class IReferenceField(IField):
    """ Marker interface for Products.Archetypes.Field.ReferenceField """
