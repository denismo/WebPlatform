from webplatform.modules import ModuleMethod
from webplatform.runtime import IAspect

__author__ = 'Denis Mikhalkin'

class MainMethodAspect(IAspect):
    def appliesTo(self, obj):
        return type(obj) == ModuleMethod and obj.name == "main" and obj.static