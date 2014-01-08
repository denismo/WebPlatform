from com.webplatform.modules import ModuleState
from com.webplatform.runner.boostrap import ioc
from llvm import *
from llvm.core import *
from llvm.ee import *

__author__ = 'Denis Mikhalkin'

class ModuleCache(object):
    def getCachedModuleFromURL(self, moduleURL):
        # TODO Implement retrieval from cache
        raise "Not implemented"

    def cacheModuleWithURL(self, moduleURL, module):
        # TODO Implement caching of module
        raise "Not implemented"


class ModuleIO(object):
    def fetchModule(self, moduleURL):
        # TODO Implement mock fetching
        raise "Not implemented"


class RuntimeException(Exception):
    pass


class AspectManager(object):
    def executeModuleAspects(self, module):
        pass

    def getMainMethodAspect(self):
        return None

    def extractModuleAspects(self, module):
        pass


class ExecutionService(object):
    def __init__(self):
        self.llvm = ExecutionEngine.new()

    def runMethod(self, method, **args):
        self.llvm.run_function(method, args)

    def registerMethodModule(self, method):
        pass

    def registerCodeModule(self, code):
        pass

class Runtime(object):

    def __init__(self):
        self.modules = list()
        self.moduleByUrl = dict()

    def getRunningModuleWithURL(self, moduleURL):
        return self.moduleByUrl.get(moduleURL)

    def registerModule(self, module):
        if module.state != ModuleState.loaded:
            return

        module.prepareForRuntime()  # throws
        module.state = ModuleState.resolved

        if not self.modules.index(module) == -1:
            self.modules.append(module)
            if module.origin is not None:
                self.moduleByUrl[module.origin] = module

    def activateModule(self, module):
        for subModule in Runtime.allModules(module):
            if subModule.state != ModuleState.resolved:
                raise RuntimeException("One of the module dependencies is not resolved")

        self.extractAspects(module)     # includes dependencies
        self.installAspects(module)     # includes dependencies

        for subModule in Runtime.allModules(module):
            subModule.state = ModuleState.active
        module.state = ModuleState.active

    def startModuleIfNecessary(self, module):
        method = self.locateMainMethod(module)
        if method is not None and method.static:
            self.runMethod(method)

    def installAspects(self, module):
        for subModule in Runtime.allModules(module):
            ioc.get(AspectManager).executeModuleAspects(subModule)

    def extractAspects(self, module):
        for subModule in Runtime.allModules(module):
            ioc.get(AspectManager).extractModuleAspects(subModule)

    @classmethod
    def allModules(cls, module):
        """
        Returns the list of all dependency modules including the parent module, with parent being the last module.
        Raises an exception if any of the dependencies don't have the module loaded
        @param module:
        """
        result = set()
        Runtime.collectModules(result, module)
        return result

    @classmethod
    def collectModules(cls, result, module):
        if module in result:
            return
        result.add(module)
        for dep in module.dependencies:
            if dep.module is None:
                raise RuntimeException("Missing module dependency %s" % dep.name)
            Runtime.collectModules(result, dep.module)

    def locateMainMethod(self, module):
        mainMethodAspect = ioc.get(AspectManager).getMainMethodAspect()
        if mainMethodAspect is None:
            return None
        for cls in module.allClasses():
            for method in cls.allStaticMethods():
                if mainMethodAspect.appliesTo(method):
                    return method
        return None

    def runMethod(self, method):
        ioc.get(ExecutionService).runMethod(method)
