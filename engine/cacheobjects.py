from threading import Lock

def to_cache(clazz):
    from django.core.cache import cache
    cache_key = clazz.__name__.lower()
    
    object_list = cache.get(cache_key)
    if object_list is None:
        object_list = clazz.objects
        cache.set(cache_key, object_list)
    return object_list

_cache_objects = {}
_cache_lock = Lock()

class ObjectMemoryCache(object):
    def __init__(self, clazz=None, key=None):
        global _cache_objects, _cache_lock
        self._key = key        
        self._clazz = clazz        
        self._clazz_name = None
        self.class_name()
        self._queryset = None
    
    def class_name(self):
        if self._clazz is not None:
            self._clazz_name = self._clazz.__name__
    
    def set_class(self, clazz):
        self._clazz = clazz
        self.class_name() 
        
    def set_key(self, key):
        self._key = key
    
    def queryset(self, queryset):
        self._queryset = queryset
    
    def add(self, key, value):
        raise NotImplemented
            
    
    def load(self, serialize=False, serializer_class=None):
        if not all( (self._clazz, self._clazz_name, self._key) ):
            raise ValueError, "Invalid values. Keys are empty!"
        
        _cache_lock.acquire()
        objs = None
        if self._queryset == None:
            objs = self._clazz.objects
        else:
            objs = self._queryset
        if len(objs) > 0:
            ''' search for key in first element '''
            obj = objs[0]
            ''' check if object has key '''
            if not hasattr(obj, self._key):
                return False, None
            local_dict = {}
            for obj in objs:
                key_value = getattr(obj, self._key)
                if not local_dict.has_key(key_value):
                    if serialize:
                        serialize = serializer_class(obj).serialize()
                        local_dict[key_value] = serialize
                        
                    else:
                        local_dict[key_value] = obj
            ''' create key by clazz name '''
            _cache_objects[self._clazz_name] = local_dict
            return True, local_dict
        _cache_lock.release()
        return False, None
    
    @staticmethod
    def get_objects():
        return _cache_objects 
    
    @staticmethod
    def get_key(clazz):
        key = clazz.__name__
        if _cache_objects.has_key(key):
            return _cache_objects.get(key)
        return None
    
    @staticmethod
    def get_subkey(clazz, key):
        obj = ObjectMemoryCache.get_key(clazz)
        if obj:
            if obj.kas_key(key):
                return obj[key]
        return None
        

def all_objects_to_cache():
    from main.models import AnswerSettings, GameType, Question, Category
    from main.response import QuestionResponse, CategoryResponse
    
    memo_obj = ObjectMemoryCache()
    """ load answer settings """
    memo_obj.set_class(AnswerSettings)
    memo_obj.set_key("seconds")
    memo_obj.load()
    
    """ load game type """
    memo_obj.set_class(GameType)
    memo_obj.set_key("id")
    memo_obj.load()
    
    """ load categories """
    memo_obj.set_class(Category)
    memo_obj.set_key("id")
    queryset = Category.objects.filter(active=True)
    memo_obj.queryset(queryset)
    memo_obj.load(serialize=True, serializer_class=CategoryResponse)
    
    """ load questions in cache """
    memo_obj.set_class(Question)
    memo_obj.set_key("id")
    queryset = Question.objects.filter(approved=True)
    memo_obj.queryset(queryset)
    memo_obj.load(serialize=True, serializer_class=QuestionResponse)
        
