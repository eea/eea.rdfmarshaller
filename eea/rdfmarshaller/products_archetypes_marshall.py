from App.class_init import InitializeClass
from zope.interface import implementer, Interface
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base


class ILayer(Interface):
    """Layering support
    """

    def initializeInstance(instance, item=None, container=None):
        """Optionally called to initialize a layer for an entire
        instance
        """

    def initializeField(instance, field):
        """Optionally called to initialize a layer for a given field
        """

    def cleanupField(instance, field):
        """Optionally called to cleanup a layer for a given field
        """

    def cleanupInstance(instance, item=None, container=None):
        """Optionally called to cleanup a layer for an entire
        instance
        """


class IMarshall(ILayer):
    """De/Marshall data.
    """

    def demarshall(instance, data, **kwargs):
        """Given the blob 'data' demarshall it and modify 'instance'
        accordingly if possible
        """

    def marshall(instance, **kwargs):
        """Returns a tuple of content-type, length, and data
        """


@implementer(IMarshall, ILayer)
class Marshaller:

    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')

    def __init__(self, demarshall_hook=None, marshall_hook=None):
        self.demarshall_hook = demarshall_hook
        self.marshall_hook = marshall_hook

    def initializeInstance(self, instance, item=None, container=None):
        dm_hook = None
        m_hook = None
        if self.demarshall_hook is not None:
            dm_hook = getattr(instance, self.demarshall_hook, None)
        if self.marshall_hook is not None:
            m_hook = getattr(instance, self.marshall_hook, None)
        instance.demarshall_hook = dm_hook
        instance.marshall_hook = m_hook

    def cleanupInstance(self, instance, item=None, container=None):
        if hasattr(aq_base(instance), 'demarshall_hook'):
            delattr(instance, 'demarshall_hook')
        if hasattr(aq_base(instance), 'marshall_hook'):
            delattr(instance, 'marshall_hook')

    def demarshall(self, instance, data, **kwargs):
        raise NotImplemented

    def marshall(self, instance, **kwargs):
        raise NotImplemented

    def initializeField(self, instance, field):
        pass

    def cleanupField(self, instance, field):
        pass

InitializeClass(Marshaller)
