from injector import Injector, inject

__author__ = 'Denis Mikhalkin'

# TODO Implement decoding of binaries as dictionaries (easier for testing)

class Resource(object):
    def __init__(self):
        self.type = ""   # Content type, e.g. image/png or binary/class
        self.name = ""   # The fully-qualified name of the resource, with namespace
        self.visibility = Visibility.default     # Visibility enum
        # The resource content depends on type and can be missing altogether


class ModuleDependencyResource(object):
    def __init__(self, dep):
        for prop in ["name", "originURL", "requiredVersion", "certificateHash", "downloadTime"]:
            setattr(self, prop, dep[prop])


class ModuleResource(Resource):
    @inject(ioc=Injector)
    def __init__(self, moduleBinary, ioc):
        super(ModuleResource, self).__init__()
        self.ioc = ioc
        self.decode(moduleBinary)

    def decode(self, moduleBinary):
        if isinstance(moduleBinary, dict):
            self.name = moduleBinary["name"]
            self.version = moduleBinary["version"]
            self.certificate = moduleBinary["certificate"]
            self.signature = moduleBinary["signature"]
            # TODO Set origin as the URL from which the binary was downloaded?
            self.origin = moduleBinary["origin"]

            self.dependencies = list()
            for dep in moduleBinary["dependencies"]:
                self.dependencies.append(ModuleDependencyResource(dep))

            self.resources = list()

            resFactory = self.ioc.get(IResourceFactory)
            for res in moduleBinary["resources"]:
                self.resources.append(resFactory.decode(res))

            # TODO Implement verification
            self.verifyModule()


class MethodResource(object):
    # name, code
    def __init__(self, methodBinary):
        self.decode(methodBinary)

    def decode(self, methodBinary):
        self.name = methodBinary["name"]
        self.parameters = MethodResource.decodeParameters(methodBinary["parameters"])
        self.returnType = MethodResource.decodeType(methodBinary["returnType"])
        self.content = methodBinary["code"]


class CodeResource(Resource):
    type = "application/x-web-code"

    def __init__(self, codeBinary):
        super(CodeResource, self).__init__()
        self.content = codeBinary["code"]  # LLVM Binary
        self.type = CodeResource.type


class ClassResource(Resource):
    type = "application/x-web-class"

    def __init__(self, classBinary):
        super(ClassResource, self).__init__()
        self.methods = list()
        self.name = ""
        self.type = ClassResource.type
        self.decode(classBinary)

    def decode(self, classBinary):
        self.name = classBinary["name"]
        for meth in classBinary["methods"]:
            self.methods.append(MethodResource(meth))


class Visibility(object):
    private = 1
    internal = 2    # Internally visible resources are visible only within the same module
    public = 3
    default = internal


class IResourceFactory(object):
    pass