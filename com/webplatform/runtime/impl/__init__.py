from injector import Injector, inject
from llvm.core import *
from llvm.ee import *

from com.webplatform.modules import ModuleState
from webplatform.runtime import IExecutionService, IRuntime, IModuleIO, IModuleCache, RuntimeException


__author__ = 'Denis Mikhalkin'

class ModuleCache(IModuleCache):
    def getCachedModuleFromURL(self, moduleURL):
        # TODO Implement retrieval from cache
        return None

    def cacheModuleWithURL(self, moduleURL, module):
        # TODO Implement caching of module
        pass


class ModuleIO(IModuleIO):
    def fetchModule(self, moduleURL):
        # TODO Implement mock fetching
        raise RuntimeException("Not implemented")


class AspectManager(object):
    def executeModuleAspects(self, module):
        pass

    def getMainMethodAspect(self):
        return None

    def extractModuleAspects(self, module):
        pass


class ExecutionService(IExecutionService):
    def __init__(self):
        emptyModule = Module.new('Dummy')
        self.llvm = ExecutionEngine.new(emptyModule)

    def runMethod(self, method, **args):
        self.llvm.run_function(method, args)

    def registerMethodModule(self, method):
        # methodModule = Module.new(method.ownerClass.ownerModule.strongName() + ":" + method.ownerClass.name + ":" + method.name)
        # TODO How about module name?
        methodModule = Module.from_assembly(method.code)
        self.llvm.add_module(methodModule)

    def registerCodeModule(self, code):
        codeModule = Module.from_assembly(code)
        self.llvm.add_module(codeModule)


class Runtime(IRuntime):

    @inject(ioc=Injector)
    def __init__(self, ioc):
        self.modules = list()
        self.moduleByUrl = dict()
        self.ioc = ioc

    def getRunningModuleWithURL(self, moduleURL):
        return self.moduleByUrl.get(moduleURL)

    def registerModule(self, module):
        if module.state != ModuleState.loaded:
            return

        module.prepareForRuntime()  # throws
        module.state = ModuleState.resolved

        if not module in self.modules:
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
            self.ioc.get(AspectManager).executeModuleAspects(subModule)

    def extractAspects(self, module):
        for subModule in Runtime.allModules(module):
            self.ioc.get(AspectManager).extractModuleAspects(subModule)

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
        if not module.dependencies is None:
            for dep in module.dependencies:
                if dep.module is None:
                    raise RuntimeException("Missing module dependency %s" % dep.name)
                Runtime.collectModules(result, dep.module)

    def locateMainMethod(self, module):
        mainMethodAspect = self.ioc.get(AspectManager).getMainMethodAspect()
        if mainMethodAspect is None:
            return None
        for cls in module.allClasses():
            for method in cls.allStaticMethods():
                if mainMethodAspect.appliesTo(method):
                    return method
        return None

    def runMethod(self, method):
        self.ioc.get(ExecutionService).runMethod(method)
