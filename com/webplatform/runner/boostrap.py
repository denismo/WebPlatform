from com.webplatform.runtime import Runtime, ModuleCache, ModuleIO
from com.webplatform.modules import Module, ModuleDependency

__author__ = 'Denis Mikhalkin'

from sys import argv, exit
import injector

ioc = injector.Injector([])


def fetchModule(moduleURL):
    module = ioc.get(Runtime).getRunningModuleWithURL(moduleURL)
    if module is not None:
        return module

    moduleCache = ioc.get(ModuleCache)
    moduleBinary = moduleCache.getCachedModuleFromURL(moduleURL)
    if moduleBinary is not None:
        moduleBinary = ioc.get(ModuleIO).fetchModule(moduleURL)     # throws
        moduleCache.cacheModuleWithURL(moduleURL, moduleBinary)

    return Module.newFromBinary(moduleBinary)


def fetchModuleFromCentral(requirement):
    # TODO There might be multiple URLs which we need to try
    raise "Not implemented"


def loadModuleDependencies(dependentModule):
    runtime = ioc.get(Runtime)
    cache = ioc.get(ModuleCache)
    for dependency in dependentModule.dependencies:
        # TODO Check download time
        requirement = dependency.moduleRequirement()
        if runtime.isModuleLoaded(requirement):
            continue
        module = cache.getCachedModuleFromRequirement(requirement)
        if module is not None:
            if dependency.originURL is not None:
                try:
                    module = fetchModule(dependency.originURL)      # throws
                except:
                    module = fetchModuleFromCentral(requirement)    # throws

        runtime.registerModule(module)
        dependency.module = module


def loadModule(moduleURL):
    module = fetchModule(moduleURL)     # throws
    if module.dependencies is not None:
        loadModuleDependencies(module)  # throws

    ioc.get(Runtime).registerModule(module)
    return module


def activateModule(mainModule):
    ioc.get(Runtime).activateModule(mainModule)


def startModule(mainModule):
    ioc.get(Runtime).startModuleIfNecessary(mainModule)


if __name__ == '__main__':
    moduleURL = argv[1]

    # Also does dependency resolution and aspect execution
    mainModule = loadModule(moduleURL)  # throws # TODO Asynchronous?
    # Notifies all the listeners that new module has been loaded. This gives them opportunity to inspect the module and
    # register it (or add manual aspects)
    # Also notifies the listeners of the module that it has been loaded
    activateModule(mainModule)          # throws
    # Notifies the module that it is active and ready to go
    startModule(mainModule)             # throws

