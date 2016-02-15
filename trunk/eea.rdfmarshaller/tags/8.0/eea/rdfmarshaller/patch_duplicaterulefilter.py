""" Patch for plone.app.contentrules.handlers.DuplicateRuleFilter
"""
from plone.app.contentrules.handlers import _get_uid
from zope.container.interfaces import IObjectRemovedEvent

def patched___call__(self, context, rule, event):
    """ Workaround: don't add the rule in the list of executed ones,
    because together with plone.app.linkintegrity it causes to don't execute
    the rule"""
    exec_context = getattr(event, 'object', context)
    uid = _get_uid(exec_context)

    if (uid, rule.__name__, ) in self.executed:
        return False
    else:
        # workaround for ObjectRemovedEvent
        if not IObjectRemovedEvent.providedBy(event):
        #end of workaround
            self.executed.add((uid, rule.__name__, ))
        return True
