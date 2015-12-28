from injector import Injector, inject
# from llvm.core import *
# from llvm.ee import *

from webplatform.modules import ModuleState, ModuleIdentifier, Module
from webplatform.runtime import IExecutionService, IRuntime, IModuleIO, IModuleCache, RuntimeException
from webplatform.runtime.impl.aspects import MainMethodAspect
import dontasq

__author__ = 'Denis Mikhalkin'


class ModuleCache(IModuleCache):

    def __init__(self):
        self.cache = dict()

    def getCachedModule(self, moduleRequirement):
        for key in self.cache:
            if moduleRequirement.matches(key):
                return self.cache[key]

        return None

    def cacheModule(self, module):
        if type(module) == Module:
            key = module.getIdentifier()
        else:
            key = ModuleIdentifier(module)
        self.cache[key] = module


class ModuleIO(IModuleIO):
    def fetchModule(self, moduleURL):
        # TODO Implement mock fetching
        raise RuntimeException("Not implemented")

class AspectManager(object):
    def __init__(self):
        self.mainMethodAspect = MainMethodAspect()

    def executeModuleAspects(self, module):
        pass

    def getMainMethodAspect(self):
        return self.mainMethodAspect

    def extractModuleAspects(self, module):
        pass


# class LLVMExecutionService(IExecutionService):
#     def __init__(self):
#         emptyModule = Module.new('Dummy')
#         self.llvm = ExecutionEngine.new(emptyModule)
#
#     def runMethod(self, method, **args):
#         retval = self.llvm.run_function(method, args)
#         if retval is not None:
#             print "Returned: %s" % str(retval.as_int())
#
#     def registerMethodModule(self, method):
#         # methodModule = Module.new(method.ownerClass.ownerModule.strongName() + ":" + method.ownerClass.name + ":" + method.name)
#         # TODO How about module name?
#         methodModule = Module.from_assembly(method.code)
#         self.llvm.add_module(methodModule)
#
#     def registerCodeModule(self, code):
#         codeModule = Module.from_assembly(code)
#         self.llvm.add_module(codeModule)
#
class PythonExecutionService(IExecutionService):


    def __init__(self):
        self.name = "PythonExecutionService"
        self.methods = dict()

    def runMethod(self, method, **args):
        retval = None
        if hasattr(method, 'code'):
            if hasattr(method, 'references'):
                for reference in method.references:
                    args[reference['runtime']['stub']] = reference['referenced'].compiledCode
            exec method.code in args
        if retval is not None:
            print "Returned: %s" % str(retval.as_int())

    def registerMethodModule(self, method):
        code = method.code
        def wrapper(argumentList):
            def _runner(*args):
                exec code in dict(zip(argumentList, args))

            return _runner

        """:type method ModuleMethod"""
        if hasattr(method, 'references'):
            for reference in method.references:
                # TODO This should really go via compiled externs of modules - so runtime needs resolve that first to avoid leakage of concepts
                fullName = reference['module']['name'] + '.' + reference['className'] + '.' + reference['methodName']
                if not fullName in self.methods:
                    raise RuntimeException('Unable to find function for reference ' + str(reference))
                reference['referenced'] = self.methods[fullName]
        self.methods[method.ownerClass.ownerModule.name + '.' + method.ownerClass.name + '.' + method.name] = method
        method.compiledCode = wrapper(method.parameters.select(lambda arg: arg.name).to_list())

    def registerCodeModule(self, code):
        pass

class Runtime(IRuntime):

    @inject(ioc=Injector)
    def __init__(self, ioc):
        self.modules = list()
        self.moduleByKey = dict()
        self.ioc = ioc

    def getRunningModule(self, moduleRequirement):
        return self.moduleByKey.get(ModuleIdentifier(moduleRequirement))

    def isModuleLoaded(self, moduleRequirement):
        return self.moduleByKey.get(ModuleIdentifier(moduleRequirement)) is not None

    def registerModule(self, module):
        if module.state != ModuleState.loaded:
            return

        module.prepareForRuntime()  # throws
        module.state = ModuleState.resolved

        if not module in self.modules:
            self.modules.append(module)
            if module.origin is not None:
                self.moduleByKey[module.getIdentifier()] = module

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
        for cls in module.classes:
            for method in cls.staticMethods():
                if mainMethodAspect.appliesTo(method):
                    return method
        return None

    def runMethod(self, method):
        self.ioc.get(IExecutionService).runMethod(method)
