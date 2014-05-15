""" Handlers for object moved events
"""
from zope.event import notify
from eea.rdfmarshaller.actions.events import ObjectMovedOrRenamedEvent
from zope.lifecycleevent.interfaces import IObjectAddedEvent, \
                                            IObjectRemovedEvent
from eea.rdfmarshaller.actions.interfaces import IObjectMovedOrRenamedEvent
from plone.app.contentrules.handlers import is_portal_factory, execute
from Products.CMFCore.interfaces import IContentish

def moved(event):
    """ When an object is renamed/moved,
    execute rules assigned to its new parent."""
    obj = event.object
    if (not event.oldParent or not
            event.newParent or
            getattr(obj, "_at_creation_flag", None)):
        return
    if is_portal_factory(obj):
        return
    elif IContentish.providedBy(obj):
        execute(event.newParent, event)
    else:
        return

def forwardevent(event):
    """ Trigger an ObjectMovedOrRenamedEvent only
    if it's not an ObjectAddedEvent or an ObjectRemovedEvent"""
    if IObjectAddedEvent.providedBy(event) \
        or IObjectRemovedEvent.providedBy(event) \
        or IObjectMovedOrRenamedEvent.providedBy(event):
        return
    notify(ObjectMovedOrRenamedEvent(event.object,
                                event.oldParent,
                                event.oldName,
                                event.newParent,
                                event.newName))
