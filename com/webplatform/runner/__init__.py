import injector
from webplatform.runtime import IRuntime, IModuleCache, IModuleIO, RuntimeException
from webplatform.modules import Module

__author__ = 'Denis Mikhalkin'

class Bootstrapper(object):
    def __init__(self, moduleRequiment, ioc):
        self.ioc = ioc
        # Also does dependency resolution and aspect execution
        mainModule = self.loadModule(moduleRequiment)  # throws # TODO Asynchronous?
        # Notifies all the listeners that new module has been loaded. This gives them opportunity to inspect the module and
        # register it (or add manual aspects)
        # Also notifies the listeners of the module that it has been loaded
        self.activateModule(mainModule)          # throws
        # Notifies the module that it is active and ready to go
        self.startModule(mainModule)             # throws

    def fetchModule(self, moduleRequirement):
        moduleBinary = self.ioc.get(IModuleIO).fetchModule(moduleRequirement)     # throws
        if moduleBinary is None:
            raise RuntimeException("Unable to load binary for " + moduleRequirement)
        return moduleBinary

    def fetchModuleFromCentral(self, requirement):
        # TODO There might be multiple URLs which we need to try
        raise "Not implemented"

    def loadModuleDependencies(self, dependentModule): # throws
        runtime = self.ioc.get(IRuntime)
        cache = self.ioc.get(IModuleCache)
        for dependency in dependentModule.dependencies:
            # TODO Check download time
            requirement = dependency.moduleRequirement()
            if runtime.isModuleLoaded(requirement):
                continue
            moduleBinary = cache.getCachedModule(requirement)
            if moduleBinary is None:
                if hasattr(dependency, 'originURL') and dependency.originURL is not None:
                    try:
                        moduleBinary = self.fetchModule(dependency.originURL)      # throws
                    except:
                        moduleBinary = self.fetchModule(requirement)    # throws
                else:
                    moduleBinary = self.fetchModule(requirement)

            module = Module.newFromBinary(moduleBinary, self.ioc)
            runtime.registerModule(module)
            dependency.module = module

    def loadModule(self, moduleRequirement):
        module = self.ioc.get(IRuntime).getRunningModule(moduleRequirement)
        if module is not None:
            return module

        moduleCache = self.ioc.get(IModuleCache)
        moduleBinary = moduleCache.getCachedModule(moduleRequirement)
        if moduleBinary is None:
            moduleBinary = self.fetchModule(moduleRequirement)     # throws
            moduleCache.cacheModule(moduleBinary)
        module = Module.newFromBinary(moduleBinary, self.ioc)
        if module.dependencies is not None:
            self.loadModuleDependencies(module)  # throws

        self.ioc.get(IRuntime).registerModule(module)
        # TODO Determine and handle cyclic dependency?
        return module

    def activateModule(self, mainModule):
        self.ioc.get(IRuntime).activateModule(mainModule)

    def startModule(self, mainModule):
        self.ioc.get(IRuntime).startModuleIfNecessary(mainModule)
