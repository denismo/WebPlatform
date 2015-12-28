import injector
from mock import Mock, patch
from webplatform.comms import ClassResource, MethodResource, IResourceFactory, ResourceFactory, ParameterKind
from webplatform.modules import ModuleRequirement
from webplatform.runner import Bootstrapper
from webplatform.runtime import IModuleIO, IRuntime, IModuleCache, IExecutionService, ITypeLookup
from webplatform.runtime.impl import Runtime, ModuleCache, ModuleIO, PythonExecutionService

__author__ = 'Denis Mikhalkin'

import unittest

# TODO: Convert Reference dictionary into attributes of an objects (create ModuleFunctionReference)
# TODO: Do proper externs resolution in Execution Service
class TestExecute(unittest.TestCase):
    moduleDef = {"name": "TestModule", "version": "1.0", "certificate": None, "signature": None, "origin": "Test",
                 "publisher": "SomePublisher", "certificateHash": "abc", "resources": [
            {"type": ClassResource.type, "name": "TestClass",
             "methods": [{"name": "main", "static": True, "code": "print 'Hello world'"}]}]}
    systemModuleDef = {"name": "System", "version": "1.0", "certificate": None, "signature": None, "origin": "Core",
                 "publisher": "System", "certificateHash": "abc", "resources": [
            {"type": ClassResource.type, "name": "System",
             "methods": [{"name": "println", "static": True, "code": "print arg",
                          "parameters":[
                              {"name":"arg", "type":"string", "kind": ParameterKind.pIn}
                          ]
                          }]}]}
    moduleWithMethodImportDef = {"name": "TestModule", "version": "1.0", "certificate": None, "signature": None, "origin": "Test",
                 "publisher": "SomePublisher", "certificateHash": "abc",
                                 "dependencies":[
                                     {"name":"System", "publisher":"System", "requiredVersion":"1.0", "certificateHash":"abc"}
                                 ],
                                 "resources": [
            {"type": ClassResource.type, "name": "TestClass",
             "methods": [
                 {"name": "main", "static": True, "code": "_println('Hello')",
                  "references":[
                      {"methodName": "println", "className": "System",
                       "module":{"name": "System", "version": "1.0", "publisher": "System", "certificateHash":"abc"},
                       "runtime":{"stub": "_println"} # Stub indicates the placeholder that the compiler put in instead of the method invocation (think call table lookup entry)
                       # It is to be replaced by runtime with the actual invocation during VM compilation
                       }
                  ]}
             ]}]}

    def testModuleRequirementRepr(self):
        req = ModuleRequirement("Test", "1.0", "Some", "abc")
        assert repr(req) == "ModuleRequirement(name=Test, version=VersionRequirement(Test (1.0)), publisher=Some, certificateHash=abc)"

    def testBindings(self):
        ioc = self.createIoc()
        assert type(ioc.get(IRuntime)) == Runtime
        assert type(ioc.get(IModuleCache)) == ModuleCache
        assert type(ioc.get(IExecutionService)) == PythonExecutionService
        assert type(ioc.get(IResourceFactory)) == ResourceFactory

    def createIoc(self, mockIO=None, mockTypeLookup=None):
        def configure(binder):
            binder.bind(IRuntime, Runtime, scope=injector.singleton)
            binder.bind(IModuleCache, ModuleCache, scope=injector.singleton)
            binder.bind(IExecutionService, PythonExecutionService, scope=injector.singleton)
            binder.bind(IResourceFactory, ResourceFactory, scope=injector.singleton)
            if mockIO is not None:
                binder.bind(IModuleIO, injector.InstanceProvider(mockIO))
            if mockTypeLookup is not None:
                binder.bind(ITypeLookup, injector.InstanceProvider(mockTypeLookup))

        ioc = injector.Injector(configure)
        return ioc

    @patch("com.webplatform.runtime.impl.ModuleIO")
    def testExecute(self, mockModuleIOWrapper):
        mockIO = mockModuleIOWrapper.return_value
        ioc = self.createIoc(mockIO)
        mockIO.fetchModule.return_value = TestExecute.moduleDef
        Bootstrapper(ModuleRequirement("TestModule", "1.0", "SomePublisher", "abc"), ioc)

    @patch("com.webplatform.runtime.impl.ModuleIO")
    def testCaching(self, mockModuleIOWrapper):
        mockIO = mockModuleIOWrapper.return_value
        ioc = self.createIoc(mockIO)

        ioc.get(IModuleCache).cacheModule(TestExecute.moduleDef)

        Bootstrapper(ModuleRequirement("TestModule", "1.0", "SomePublisher", "abc"), ioc)

    @patch("com.webplatform.runtime.impl.ModuleIO")
    @patch("com.webplatform.runtime.ITypeLookup")
    def testMethodImport(self, mockModuleIOWrapper, mockModuleTypeLookup):
        mockIO = mockModuleIOWrapper.return_value
        mockTypeLookup = mockModuleTypeLookup.return_value
        ioc = self.createIoc(mockIO, mockTypeLookup)
        mockTypeLookup.lookup.return_value = None

        ioc.get(IModuleCache).cacheModule(TestExecute.systemModuleDef)
        ioc.get(IModuleCache).cacheModule(TestExecute.moduleWithMethodImportDef) # This should print

        Bootstrapper(ModuleRequirement("TestModule", "1.0", "SomePublisher", "abc"), ioc)
