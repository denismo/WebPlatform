import injector
from webplatform.runner import Bootstrapper
from webplatform.runtime import IModuleIO, IRuntime, IModuleCache
from webplatform.runtime.impl import Runtime, ModuleCache

__author__ = 'adminuser'

import unittest

class TestExecute(unittest.TestCase):

    def testExecute(self):
        def configure(binder):
            binder.bind(IRuntime, Runtime)
            binder.bind(IModuleCache, ModuleCache)
            binder.bind(IModuleIO, MockModuleIO)
        ioc = injector.Injector(configure)
        boot = Bootstrapper("", ioc)


class MockModuleIO:
    def fetchModule(self, moduleURL):
        return None