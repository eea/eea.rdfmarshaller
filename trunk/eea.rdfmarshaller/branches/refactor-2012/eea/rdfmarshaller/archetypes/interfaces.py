from zope.interface import Interface, Attribute
from Products.Archetypes.interfaces import IField


class IArchetype2Surf(IObject2Surf):
    """ IObject2Surf implementations for Archetype objects"""


class IATField2Surf(Interface):
    """ Extract values from Fields, to store them in the surf session """

    def get_value(context):
        """ Returns the value in RDF format """

    exportable = Attribute("Is this field exportable to RDF?")


#now comes the marker interfaces

class IATVocabulary(Interface):
    """ Marker interface for ATVocabularyManager Simple Vocabulary """


class IATVocabularyTerm(Interface):
    """ Marker interface for ATVocabularyManager Simple Term """


class IReferenceField(IField):
    """ Marker interface for Products.Archetypes.Field.ReferenceField """


class ITextField(IField):
    """ Marker interface for Products.Archetypes.Field.TextField """

