from injector import Injector
from webplatform.runner import Bootstrapper
from webplatform.runtime import IModuleIO, IModuleCache, IRuntime
from webplatform.runtime.impl import ModuleIO, ModuleCache, Runtime

__author__ = 'Denis Mikhalkin'

from sys import argv

if __name__ == '__main__':
    moduleURL = argv[1]
    ioc = Injector([])
    ioc.binder.bind(IModuleIO, ModuleIO)
    ioc.binder.bind(IRuntime, Runtime)
    ioc.binder.bind(IModuleCache, ModuleCache)
    Bootstrapper(moduleURL, ioc)

