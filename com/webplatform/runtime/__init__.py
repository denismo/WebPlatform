from abc import abstractmethod
from abc import ABCMeta


class IExecutionService(object):
    pass

class IRuntime(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def isModuleLoaded(self, moduleRequirement):
        pass


class IModuleCache(object):
    def cacheModule(self, module):
        pass
    def getCachedModule(self, moduleRequirement):
        pass

class IModuleIO(object):
    pass

# TODO Potential hook into language runtime? In order to provide native types (e.g. native tuple or list) as opposed to class-implemented types
class ITypeLookup(object):
    pass

class IAspect(object):
    def appliesTo(self, obj):
        pass


class RuntimeException(BaseException):
    pass

