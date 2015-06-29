""" Custom ObjectMovedOrRenamedEvent"""
from eea.rdfmarshaller.actions.interfaces import IObjectMovedOrRenamedEvent
from zope.lifecycleevent import ObjectMovedEvent
from zope.interface import implements

class ObjectMovedOrRenamedEvent(ObjectMovedEvent):
    """ObjectMovedOrRenamedEvent"""
    implements(IObjectMovedOrRenamedEvent)
