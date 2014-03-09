import injector
from mock import Mock, patch
from webplatform.comms import ClassResource, MethodResource
from webplatform.runner import Bootstrapper
from webplatform.runtime import IModuleIO, IRuntime, IModuleCache, IExecutionService
from webplatform.runtime.impl import Runtime, ModuleCache, ModuleIO, ExecutionService

__author__ = 'Denis Mikhalkin'

import unittest

class TestExecute(unittest.TestCase):

    @patch("com.webplatform.runtime.impl.ModuleIO")
    def testExecute(self, mockModuleIOWrapper):
        mockIO = mockModuleIOWrapper.return_value
        def configure(binder):
            binder.bind(IRuntime, Runtime)
            binder.bind(IModuleCache, ModuleCache)
            binder.bind(IModuleIO, injector.InstanceProvider(mockIO))
            binder.bind(IExecutionService, ExecutionService)
        ioc = injector.Injector(configure)

        mockIO.fetchModule.return_value = {
            "name": "TestModule",
            "version": "1.0",
            "certificate": None,
            "signature": None,
            "origin": "Test",
            "resources": list({
                "type": ClassResource.type,
                "name": "TestClass",
                "methods": list({
                    "name": "main",
                    "static": True
                })
            })
        }
        # TODO: Next time: Implement resource factory
        Bootstrapper("", ioc)
