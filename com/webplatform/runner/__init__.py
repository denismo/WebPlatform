import injector
from webplatform.runtime import IRuntime, IModuleCache, IModuleIO, RuntimeException
from webplatform.modules import Module

__author__ = 'Denis Mikhalkin'

class Bootstrapper(object):
    def __init__(self, moduleURL, ioc):
        self.ioc = ioc
        # Also does dependency resolution and aspect execution
        mainModule = self.loadModule(moduleURL)  # throws # TODO Asynchronous?
        # Notifies all the listeners that new module has been loaded. This gives them opportunity to inspect the module and
        # register it (or add manual aspects)
        # Also notifies the listeners of the module that it has been loaded
        self.activateModule(mainModule)          # throws
        # Notifies the module that it is active and ready to go
        self.startModule(mainModule)             # throws


    def fetchModule(self, moduleURL):
        module = self.ioc.get(IRuntime).getRunningModuleWithURL(moduleURL)
        if module is not None:
            return module

        moduleCache = self.ioc.get(IModuleCache)
        moduleBinary = moduleCache.getCachedModuleFromURL(moduleURL)
        if moduleBinary is None:
            moduleBinary = self.ioc.get(IModuleIO).fetchModule(moduleURL)     # throws
            if moduleBinary is None:
                raise RuntimeException("Unable to load binary for " + moduleURL)
            moduleCache.cacheModuleWithURL(moduleURL, moduleBinary)

        return Module.newFromBinary(moduleBinary, self.ioc)


    def fetchModuleFromCentral(self, requirement):
        # TODO There might be multiple URLs which we need to try
        raise "Not implemented"


    def loadModuleDependencies(self, dependentModule):
        runtime = self.ioc.get(IRuntime)
        cache = self.ioc.get(IModuleCache)
        for dependency in dependentModule.dependencies:
            # TODO Check download time
            requirement = dependency.moduleRequirement()
            if runtime.isModuleLoaded(requirement):
                continue
            module = cache.getCachedModuleFromRequirement(requirement)
            if module is not None:
                if dependency.originURL is not None:
                    try:
                        module = self.fetchModule(dependency.originURL)      # throws
                    except:
                        module = self.fetchModuleFromCentral(requirement)    # throws

            runtime.registerModule(module)
            dependency.module = module


    def loadModule(self, moduleURL):
        module = self.fetchModule(moduleURL)     # throws
        if module.dependencies is not None:
            self.loadModuleDependencies(module)  # throws

        self.ioc.get(IRuntime).registerModule(module)
        return module


    def activateModule(self, mainModule):
        self.ioc.get(IRuntime).activateModule(mainModule)


    def startModule(self, mainModule):
        self.ioc.get(IRuntime).startModuleIfNecessary(mainModule)
