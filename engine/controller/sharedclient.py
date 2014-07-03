import sys
import traceback
import logging
from multiprocessing import Process
from multiprocessing.managers import BaseManager, BaseProxy, DictProxy
from collections import defaultdict

logging.getLogger("SharedClient")
logging.basicConfig(level = logging.DEBUG,
                    format = "[%(asctime)s] - %(name)s - %(levelname)s: %(message)s",
                    datefmt = "%H:%M:%S"                    
                    )

class PluginManager(BaseManager):
    pass

class PluginProxy(BaseProxy):
    pass

AUTH_KEY = "'=f_kak2m9mt05om%t9tcv!u%_lj*0brj=$l=w4c^zti1%j^=+o'"
DEFAULT_ADDR = ('127.0.0.1', 50000)

class SharedPlugin(object):
    def __init__(self, addr, auth_key=''):
        self.manager = PluginManager(address=addr, authkey=auth_key)
    
    def register(self, plugin, methods):
        self.manager.register(plugin, exposed=methods)
    
    def get_manager(self):
        return self.manager
    
    def connect(self):
        try:
            self.manager.connect()
        except:
            traceback.print_exc()
 
class PluginManipulator(object):
    
    @staticmethod
    def get_plugin(plugin, methods):
        shared = SharedPlugin(DEFAULT_ADDR, AUTH_KEY)
        shared.register(plugin, methods)
        shared.connect()
        
        manager = shared.get_manager()
        return manager.solver()
        

def main(args):
    key, value = args[1], args[2]

    shared = SharedPlugin(DEFAULT_ADDR, AUTH_KEY)
    shared.register('solver', ['get_len', 'add_key', 'get_dict'])
    shared.connect()
    
    manager = shared.get_manager()
    plugin = manager.solver()
    shared_value = plugin.add_key(key, value)
    
    logging.info("shared value: %s " % (str(shared_value) ) )
    
    #SolverManager.register('solver', exposed=['get_len', 'add_key', 'get_dict'])

    #manager = SolverManager(address=('127.0.0.1', 50000), authkey='abc')
    #manager.connect()
    
    
    #logging.info("key - value: %s - %s " % (key, str(value) ) )
    #solver = manager.solver()
    #shared_value = solver.add_key(key, value)
    #logging.info("shared value: %s " % (str(shared_value) ) )
    
if __name__ == '__main__':
    main(sys.argv)
    sys.exit()
