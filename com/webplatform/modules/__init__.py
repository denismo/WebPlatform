from injector import inject, Injector
from com.webplatform.runtime import IExecutionService
from webplatform.comms import CodeResource, ClassResource, ModuleResource

__author__ = 'Denis Mikhalkin'


class ModuleClass(object):
    def __init__(self, classRes):
        self.name = classRes.name

        self.methods = dict()
        for methRes in classRes.methods:
            meth = ModuleMethod(methRes)
            self.methods[meth.name] = meth

    def prepare(self):
        for meth in self.methods:
            meth.prepare()


class ModuleMethod(object):
    @inject(ioc=Injector)
    def __init__(self, ownerClass, methodRes, ioc):
        self.ownerClass = ownerClass
        self.name = methodRes.name
        self.code = methodRes.code
        self.ioc = ioc

    def prepare(self):
        pass
        self.ioc.get(IExecutionService).registerMethodModule(self, self.code)


class Module(object):
    @inject(ioc=Injector)
    def __init__(self, ioc):
        self.ioc = ioc
        self.version = "1.0"
        self.name = "com.webplatform.module1"
        # self.signature = "signature"
        # self.certificate = "certificate"
        # self.origin = "http://www.webminivm.com/modules?module={name}&version={version}"
        self.dependencies = list()     # list of ModuleDependency
        self.resources = list()        # list of Resource
        self.state = ModuleState.loaded
        self.classes = list()

    @classmethod
    def newFromBinary(cls, moduleBinary, ioc):
        module = ioc.get(Module)
        module.init(ModuleResource(moduleBinary))
        return module


    def init(self, moduleResource):
        self.name = moduleResource.name
        self.version = moduleResource.version
        if moduleResource.dependencies is not None:
            for dep in moduleResource.dependencies:
                self.dependencies.append(ModuleDependency(dep))
        if moduleResource.resources is not None:
            for res in moduleResource.resources:
                self.resources.append(res)


    def prepareForRuntime(self):
        execService = self.ioc.get(IExecutionService)

        def prepareCode(code):
            execService.registerCodeModule(self, code)

        def prepareClass(cls):
            clsObj = ModuleClass(cls)
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


class ModuleRequirement(object):
    def __init__(self, name, requiredVersion, certificateHash):
        self.name = name
        self.requiredVersion = requiredVersion
        self.certificateHash = certificateHash


class ModuleDependency(object):
    def __init__(self, dep):
        for prop in ["name", "originURL", "requiredVersion", "certificateHash", "downloadTime"]:
            setattr(self, prop, getattr(dep, prop))

        self.requiredVersion = VersionRequirement(self.requiredVersion)

        # self.requiredVersion = None  # instance of VersionRequirement
        # self.name = ""
        # self.originURL = None        # Optional - origin hint, use central if not provided or failed
        # self.certificateHash = ""
        # self.downloadTime = ""       # one of 'immediate', 'background', 'ondemand'
        self.module = None           # instance of Module

    def moduleRequirement(self):
        return ModuleRequirement(self.name, self.requiredVersion, self.certificateHash)


class VersionRequirement(object):
    def __init__(self, reqStr):
        self.upperBound = ("", True)     # True/False for inclusive/exclusive
        self.lowerBound = ("", True)
        # TODO Decode reqStr



################ ENUMS #################


class ModuleState(object):
    loaded = 1
    resolved = 2
    active = 3
    started = 4
