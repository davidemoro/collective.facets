from zope.interface import implements, alsoProvides
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import RequiredMissing
from plone.registry.interfaces import IRecordsProxy
from plone.registry.recordsproxy import RecordsProxy, RecordsProxyCollection
from userlist import ListMixin
from zope import schema
import re

_marker = object()

def facetId(name):
    return "facet_" + re.sub("\W","", name)

class ComplexRecordsProxy(RecordsProxy):
    """A proxy that maps an interface to a number of records, including collections of complex records
    """

    implements(IRecordsProxy) 

    def __getattr__(self, name):
        if name not in self.__schema__:
            raise AttributeError(name)
        field = self.__schema__[name]
        if type(field) in [schema.List,schema.Tuple]:
            prefix = self.__prefix__ + name
            factory = None
            return RecordsProxyList(self.__registry__, field.value_type.schema, False, self.__omitted__, prefix, factory)
        elif type(field) in [schema.Dict]:
            prefix = self.__prefix__ + name
            factory = None
            return RecordsProxyCollection(self.__registry__, field.value_type.schema, False, self.__omitted__, prefix, factory)
        else:
            value = self.__registry__.get(self.__prefix__ + name, _marker)
            if value is _marker:
                value = self.__schema__[name].missing_value
            return value

    def __setattr__(self, name, value):
        if name in self.__schema__:
            full_name = self.__prefix__ + name
            field = self.__schema__[name]
            if type(field) in [schema.List,schema.Tuple]:
                proxy = self.__getattr__(name)
                proxy[:] = value
            elif type(field) in [schema.Dict]:
                proxy = self.__getattr__(name)
                proxy[:] = value
            else:
                if full_name not in self.__registry__:
                    raise AttributeError(name)
                self.__registry__[full_name] = value
        else:
            self.__dict__[name] = value


class RecordsProxyList(ListMixin):
    """A proxy that represents a List of RecordsProxy objects. Stored as prefix+"/i0001" where the number is the index
    """

    def __init__(self, registry, schema, check=True, omitted=(), prefix=None, factory=None):
        self.map = RecordsProxyCollection(registry, schema, check, omitted, prefix, factory)
#        self.data = [v for k,v in sorted(self.map.items())]

    def _get_element(self, i):
        return self.map[self.genKey(i)]

    def _set_element(self, index, value):
        self.map[self.genKey(index)] = value

    def __len__(self):
        return len(self.map)

    def _resize_region(self, start, end, new_size):
        #move everything along one
        offset = new_size - (end - start)
        if offset > 0:
            moves = range(end-1, start, -1)
        else:
            moves = range(start, end, +1)
        for i in moves:
                self.map[self.genKey(i+offset)] = self.map[self.genKey(i)]
        # remove any additional at the end
        for i in range(len(self.map)+offset, len(self.map)):
            del self.map[self.genKey(i)]

    def __iter__(self):
        for k,v in sorted(self.map.items()):
            yield v

#    def _constructor(self, iterable):
#        proxy =



    def genKey(self, index):
        index_prefix = "i"
        return "%s%05d" %(index_prefix, index)

