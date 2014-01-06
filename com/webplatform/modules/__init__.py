from com.webplatform.runner.boostrap import ioc

__author__ = 'Denis Mikhalkin'


class Module(object):
    version = "1.0"
    name = "com.webplatform.module1"
    signature = "signature"
    certificate = "certificate"
    origin = "http://www.webminivm.com/modules?module={name}&version={version}"
    dependencies = None     # list of ModuleDependency
    resources = None        # list of Resource
    state = ModuleState.loaded

    @classmethod
    def newFromBinary(cls, moduleBinary):
        module = ioc.get(Module)
        module.decode(moduleBinary)
        return module

    def decode(self, moduleBinary):
        pass

    def prepareForRuntime(self):
        # TODO Extract classes, interpret (JIT?), register them
        pass

class ModuleRequirement(object):
    def __init__(self, name, requiredVersion, certificateHash):
        self.name = name
        self.requiredVersion = requiredVersion
        self.certificateHash = certificateHash


class ModuleDependency(object):
    requiredVersion = None  # instance of VersionRequirement
    name = ""
    originURL = None        # Optional - origin hint, use central if not provided or failed
    certificateHash = ""
    downloadTime = ""       # one of 'immediate', 'background', 'ondemand'
    module = None           # instance of Module

    def moduleRequirement(self):
        return ModuleRequirement(self.name, self.requiredVersion, self.certificateHash)


class VersionRequirement(object):
    upperBound = ("", True)     # True/False for inclusive/exclusive
    lowerBound = ("", True)


class Resource(object):
    type = ""   # Content type, e.g. image/png or binary/class
    name = ""   # The fully-qualified name of the resource, with namespace
    visibility = Visibility.default     # Visibility enum
    # The resource content depends on type and can be missing altogether


class CodeResource(Resource):
    content = None  # LLVM Binary

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
