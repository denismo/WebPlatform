from injector import Injector, inject
from webplatform.runtime import ITypeLookup, RuntimeException
import dontasq

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
            self.certificateHash = moduleBinary["certificateHash"]
            self.signature = moduleBinary["signature"]
            self.publisher = moduleBinary["publisher"]
            # TODO Set origin as the URL from which the binary was downloaded?
            self.origin = moduleBinary["origin"]

            self.dependencies = list()
            if "dependencies" in moduleBinary:
                for dep in moduleBinary["dependencies"]:
                    self.dependencies.append(ModuleDependencyResource(dep))

            self.resources = list()

            resFactory = self.ioc.get(IResourceFactory)
            if "resources" in moduleBinary:
                for res in moduleBinary["resources"]:
                    self.resources.append(resFactory.decode(res))

            # TODO Implement verification
            self.verifyModule()
        else:
            raise RuntimeException("Unsupported module binary type " + type(moduleBinary))

    def verifyModule(self):
        # TODO Implement module verification
        pass


class TypedValue(object):
    @inject(ioc=Injector)
    def __init__(self, typeSpec, ioc):
        typeLookup = ioc.get(ITypeLookup)
        self.type = typeLookup.lookup(typeSpec)


class NamedTypedValue(TypedValue):
    @inject(ioc=Injector)
    def __init__(self, name, typeSpec, ioc):
        super(NamedTypedValue, self).__init__(typeSpec, ioc)
        self.name = name


class MethodParameter(NamedTypedValue):
    @inject(ioc=Injector)
    def __init__(self, parameterSpec, ioc):
        super(NamedTypedValue, self).__init__(parameterSpec["name"], parameterSpec["type"], ioc)
        self.kind = parameterSpec["kind"]   # ParameterKind - in, out, ref


class MethodResource(object):
    # name, code
    def __init__(self, methodBinary):
        self.name = methodBinary["name"]
        if "parameters" in methodBinary:
            self.parameters = methodBinary["parameters"].map(lambda param: MethodParameter(param))
        if "returnType" in methodBinary:
            self.returnType = TypedValue(methodBinary["returnType"])
        if "code" in methodBinary:
            self.content = methodBinary["code"]
        self.static = methodBinary["static"]


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
        self.type = ClassResource.type
        self.name = classBinary["name"]
        self.methods = map(lambda method: MethodResource(method), classBinary["methods"])


class Visibility(object):
    private = 1     # Private resources are visible only within the same module
    internal = 2    # Internally visible resources are visible only within the same publisher
    public = 3
    default = internal


class IResourceFactory(object):
    pass # TODO Implement resource factory


class ResourceFactory(IResourceFactory):
    resourceMap = {ClassResource.type: ClassResource, CodeResource.type: CodeResource}
    def decode(self, binaryResource):
        resource_type = binaryResource["type"]
        if resource_type in ResourceFactory.resourceMap:
            return ResourceFactory.resourceMap[resource_type](binaryResource)
        return None


class ParameterKind(object):
    pIn = 1
    pOut = 2
    pRef = 4

