
class IExecutionService(object):
    pass

class IRuntime(object):
    pass

class IModuleCache(object):
    pass

class IModuleIO(object):
    pass

# TODO Potential hook into language runtime? In order to provide native types (e.g. native tuple or list) as opposed to class-implemented types
class ITypeLookup(object):
    pass


class RuntimeException(BaseException):
    pass