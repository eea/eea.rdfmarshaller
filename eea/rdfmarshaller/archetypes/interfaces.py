""" Archetypes Interfaces
"""
from eea.rdfmarshaller.interfaces import IField2Surf, IGenericObject2Surf
from Products.Archetypes.interfaces import IField
from zope.interface import Attribute, Interface


class IArchetype2Surf(IGenericObject2Surf):
    """ IObject2Surf implementations for Archetype objects

    This interface is only used to describe the Archetype2Surf
    implementation. The IObject2Surf interface should be used as
    adapter interface
    """

    dc_map = Attribute(u"Mapping of field names to rdf names, for which  "
                       u"the prefix will be dcterms")
    field_map = Attribute(u"Mapping of fields to rdf names. It can be used "
                          u"to remap the field names in the rdf output ")
    blacklist_map = Attribute(u"A list of field names for fields that "
                              u"won't be exported")


class IATField2Surf(IField2Surf):
    """ Extract values from Fields, to store them in the surf session """


class IATVocabulary(Interface):
    """ Marker interface for ATVocabularyManager Simple Vocabulary """


class IATVocabularyTerm(Interface):
    """ Marker interface for ATVocabularyManager Simple Term """


class IReferenceField(IField):
    """ Marker interface for Products.Archetypes.Field.ReferenceField """


class ITextField(IField):
    """ Marker interface for Products.Archetypes.Field.TextField """
