from webplatform.modules import ModuleMethod
from webplatform.runtime import IAspect

__author__ = 'Denis Mikhalkin'

class MainMethodAspect(IAspect):
    def appliesTo(self, obj):
        return obj is ModuleMethod and obj.name == "main"