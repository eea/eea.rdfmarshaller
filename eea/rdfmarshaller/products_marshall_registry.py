""" Python 3 compatibility
"""


class RegistryItem:
    """ RegistryItem
    """
    def __init__(self, name, title, factory):
        self.name = name
        if not title:
            title = name
        self.title = title
        self.factory = factory

    def info(self):
        return {'name': self.name,
                'title': self.title}

    def create(self, id, title, expression, component_name):
        return self.factory(id, title or self.title, expression,
                            component_name)


comp_registry = {}


def registerComponent(name, title, component):
    comp_registry[name] = RegistryItem(name, title, component)


def getComponent(name):
    return comp_registry[name].factory()
