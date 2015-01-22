""" Custom event for Object moved or renamed """
from zope.lifecycleevent.interfaces import IObjectMovedEvent

class IObjectMovedOrRenamedEvent(IObjectMovedEvent):
    """IObjectMovedOrRenamedEvent
    """