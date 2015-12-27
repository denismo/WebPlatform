import injector
from mock import Mock, patch
from webplatform.comms import ClassResource, MethodResource, IResourceFactory, ResourceFactory
from webplatform.modules import ModuleRequirement
from webplatform.runner import Bootstrapper
from webplatform.runtime import IModuleIO, IRuntime, IModuleCache, IExecutionService
from webplatform.runtime.impl import Runtime, ModuleCache, ModuleIO, PythonExecutionService

__author__ = 'Denis Mikhalkin'

import unittest

# TODO: Focus then on designing export/import between modules
class TestExecute(unittest.TestCase):
    moduleDef = {"name": "TestModule", "version": "1.0", "certificate": None, "signature": None, "origin": "Test",
                 "publisher": "SomePublisher", "certificateHash": "abc", "resources": [
            {"type": ClassResource.type, "name": "TestClass",
             "methods": [{"name": "main", "static": True, "code": "print 'Hello world'"}]}]}

    def testBindings(self):
        def configure(binder):
            binder.bind(IRuntime, Runtime, scope=injector.singleton)
            binder.bind(IModuleCache, ModuleCache, scope=injector.singleton)
            binder.bind(IExecutionService, PythonExecutionService, scope=injector.singleton)
            binder.bind(IResourceFactory, ResourceFactory, scope=injector.singleton)
        ioc = injector.Injector(configure)
        assert type(ioc.get(IRuntime)) == Runtime
        assert type(ioc.get(IModuleCache)) == ModuleCache
        assert type(ioc.get(IExecutionService)) == PythonExecutionService
        assert type(ioc.get(IResourceFactory)) == ResourceFactory


    @patch("com.webplatform.runtime.impl.ModuleIO")
    def testExecute(self, mockModuleIOWrapper):
        mockIO = mockModuleIOWrapper.return_value
        def configure(binder):
            binder.bind(IRuntime, Runtime, scope=injector.singleton)
            binder.bind(IModuleCache, ModuleCache, scope=injector.singleton)
            binder.bind(IModuleIO, injector.InstanceProvider(mockIO))
            binder.bind(IExecutionService, PythonExecutionService, scope=injector.singleton)
            binder.bind(IResourceFactory, ResourceFactory, scope=injector.singleton)
        ioc = injector.Injector(configure)

        mockIO.fetchModule.return_value = TestExecute.moduleDef
        Bootstrapper(ModuleRequirement("TestModule", "1.0", "SomePublisher", "abc"), ioc)

    @patch("com.webplatform.runtime.impl.ModuleIO")
    def testCaching(self, mockModuleIOWrapper):
        mockIO = mockModuleIOWrapper.return_value
        def configure(binder):
            binder.bind(IRuntime, Runtime, scope=injector.singleton)
            binder.bind(IModuleCache, ModuleCache, scope=injector.singleton)
            binder.bind(IModuleIO, injector.InstanceProvider(mockIO))
            binder.bind(IExecutionService, PythonExecutionService, scope=injector.singleton)
            binder.bind(IResourceFactory, ResourceFactory, scope=injector.singleton)
        ioc = injector.Injector(configure)

        ioc.get(IModuleCache).cacheModule(TestExecute.moduleDef)

        Bootstrapper(ModuleRequirement("TestModule", "1.0", "SomePublisher", "abc"), ioc)
