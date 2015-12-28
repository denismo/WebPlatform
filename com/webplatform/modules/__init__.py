from injector import inject, Injector
from distlib.version import NormalizedVersion, NormalizedMatcher
from webplatform.runtime import IExecutionService, IRuntime, RuntimeException
from webplatform.comms import CodeResource, ClassResource, ModuleResource
import dontasq

__author__ = 'Denis Mikhalkin'

class ModuleIdentifier(object):
    def __init__(self, module):
        self.publisher = module["publisher"]
        self.name = module["name"]
        self.version = module["version"]
        self.certificateHash = module["certificateHash"]

class ModuleClass(object):
    @inject(ioc=Injector)
    def __init__(self, ioc):
        self.ioc = ioc

    def init(self, ownerModule, classRes):
        self.name = classRes.name
        self.ownerModule = ownerModule

        self.methods = dict()
        for methRes in classRes.methods:
            meth = self.ioc.get(ModuleMethod)
            meth.init(self, methRes)
            self.methods[meth.name] = meth

    def prepare(self):
        for meth in self.methods.values():
            meth.prepare()

    def staticMethods(self):
        return self.methods.values().where(lambda meth: meth.static).to_list()

class ModuleMethod(object):
    @inject(ioc=Injector)
    def __init__(self, ioc):
        self.ioc = ioc

    def init(self, ownerClass, methodRes):
        """:type ownerClass ModuleClass"""
        self.ownerClass = ownerClass
        self.name = methodRes.name
        self.code = methodRes.content if hasattr(methodRes, 'content') else None
        self.static = methodRes.static
        if hasattr(methodRes, 'references'):
            self.references = methodRes.references

        self.parameters = list()
        if hasattr(methodRes, 'parameters'):
            self.parameters = methodRes.parameters


    def prepare(self):
        execService = self.ioc.get(IExecutionService)
        execService.registerMethodModule(self)


class Module(object):
    @inject(ioc=Injector)
    def __init__(self, ioc):
        self.ioc = ioc
        self.version = "1.0" # These are really just dummy values. Initialisation happens in the init() method
        self.name = "com.webplatform.module1" # These are really just dummy values. Initialisation happens in the init() method
        # self.signature = "signature"
        # self.certificate = "certificate"
        # self.origin = "http://www.webminivm.com/modules?module={name}&version={version}"
        self.dependencies = list()      # list of ModuleDependency
        self.resources = list()         # list of Resource
        self.state = ModuleState.loaded
        self.classes = list()           # list of ModuleClass

    @classmethod
    def newFromBinary(cls, moduleBinary, ioc):
        module = ioc.get(Module)
        module.init(ModuleResource(moduleBinary, ioc))
        return module

    def init(self, moduleResource):
        self.name = moduleResource.name
        self.version = moduleResource.version
        self.origin = moduleResource.origin
        self.publisher = moduleResource.publisher
        self.certificateHash = moduleResource.certificateHash
        if moduleResource.dependencies is not None:
            for dep in moduleResource.dependencies:
                self.dependencies.append(ModuleDependency(dep))
        if moduleResource.resources is not None:
            for res in moduleResource.resources:
                self.resources.append(res)

    def getIdentifier(self):
        return ModuleIdentifier(self)

    def prepareForRuntime(self):
        execService = self.ioc.get(IExecutionService)

        def prepareCode(code):
            execService.registerCodeModule(self, code)

        def prepareClass(cls):
            clsObj = self.ioc.get(ModuleClass)
            clsObj.init(self, cls)
            self.classes.append(clsObj)
            clsObj.prepare()

        if self.resources is not None:
            for res in self.resources:
                if Module.isCode(res):
                    prepareCode(res)
                elif Module.isClass(res):
                    prepareClass(res)

    @classmethod
    def isCode(cls, res):
        return res.type == CodeResource.type

    @classmethod
    def isClass(cls, res):
        return res.type == ClassResource.type

    def __getitem__(self, item):
        return getattr(self, item)


class ModuleRequirement(object):
    def __init__(self, name, version, publisher, certificateHash):
        self.name = name
        self.version = VersionRequirement(name, version)
        self.certificateHash = certificateHash
        self.publisher = publisher

    def __getitem__(self, item):
        return getattr(self, item)

    def matches(self, moduleOrKey):
        if type(moduleOrKey) == Module:
            moduleOrKey = moduleOrKey.getIdentifier()
        if type(moduleOrKey) == ModuleIdentifier:
            return self.name == moduleOrKey.name and self.version.matches(moduleOrKey.version) and \
                   self.certificateHash == moduleOrKey.certificateHash and self.publisher == moduleOrKey.publisher
        else:
            raise RuntimeException("Unexpected value for matching module requirement: " + moduleOrKey)

    def __repr__(self):
        return "ModuleRequirement(name=%(name)s, version=%(version)s, publisher=%(publisher)s, certificateHash=%(certificateHash)s)" % self.__dict__

class ModuleDependency(object):
    def __init__(self, dep):
        for prop in ["name", "originURL", "requiredVersion", "certificateHash", "downloadTime", "publisher"]:
            if hasattr(dep, prop):
                setattr(self, prop, getattr(dep, prop))

        # self.requiredVersion = None  # instance of VersionRequirement
        # self.name = ""
        # self.originURL = None        # Optional - origin hint, use central if not provided or failed
        # self.certificateHash = ""
        # self.downloadTime = ""       # one of 'immediate', 'background', 'ondemand'
        self.module = None           # instance of Module

    def moduleRequirement(self):
        return ModuleRequirement(self.name, self.requiredVersion, self.publisher, self.certificateHash)


class VersionRequirement(object):
    def __init__(self, name, reqStr):
        # See http://pythonhosted.org/distlib/tutorial.html#using-the-version-api
        self.requirement = NormalizedMatcher('%s (%s)' % (name, reqStr))

    def matches(self, module):
        if type(module) == str:
            return self.requirement.match(NormalizedVersion(module))
        elif type(module) == Module:
            return self.requirement.match(NormalizedVersion(module.version))

    def __repr__(self):
        return "VersionRequirement(%s)" % self.requirement

################ ENUMS #################


class ModuleState(object):
    loaded = 1
    resolved = 2
    active = 3
    started = 4
