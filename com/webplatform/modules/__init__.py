from injector import inject, Injector
from com.webplatform.runtime import IExecutionService

__author__ = 'Denis Mikhalkin'


class ModuleClass(object):
    def __init__(self, classRes):
        self.name = classRes["name"]

        self.methods = dict()
        for methRes in classRes["methods"]:
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
        self.signature = "signature"
        self.certificate = "certificate"
        self.origin = "http://www.webminivm.com/modules?module={name}&version={version}"
        self.dependencies = None     # list of ModuleDependency
        self.resources = None        # list of Resource
        self.state = ModuleState.loaded
        self.classes = list()

    @classmethod
    def newFromBinary(cls, moduleBinary, ioc):
        module = ioc.get(Module)
        module.decode(moduleBinary)
        return module

    def decode(self, moduleBinary):
        pass

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
    def __init__(self):
        self.requiredVersion = None  # instance of VersionRequirement
        self.name = ""
        self.originURL = None        # Optional - origin hint, use central if not provided or failed
        self.certificateHash = ""
        self.downloadTime = ""       # one of 'immediate', 'background', 'ondemand'
        self.module = None           # instance of Module

    def moduleRequirement(self):
        return ModuleRequirement(self.name, self.requiredVersion, self.certificateHash)


class VersionRequirement(object):
    def __init__(self):
        self.upperBound = ("", True)     # True/False for inclusive/exclusive
        self.lowerBound = ("", True)


class Resource(object):
    def __init__(self):
        self.type = ""   # Content type, e.g. image/png or binary/class
        self.name = ""   # The fully-qualified name of the resource, with namespace
        self.visibility = Visibility.default     # Visibility enum
        # The resource content depends on type and can be missing altogether


class CodeResource(Resource):
    type = "application/x-web-code"

    def __init__(self):
        super(CodeResource, self).__init__()
        self.content = None  # LLVM Binary


class ClassResource(Resource):
    type = "application/x-web-class"

    def __init__(self):
        super(ClassResource, self).__init__()

################ ENUMS #################


class Visibility(object):
    private = 1
    internal = 2    # Internally visible resources are visible only within the same module
    public = 3
    default = internal


class ModuleState(object):
    loaded = 1
    resolved = 2
    active = 3
    started = 4
