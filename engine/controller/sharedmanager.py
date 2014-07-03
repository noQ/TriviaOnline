import logging
import traceback
from multiprocessing.managers import BaseManager, BaseProxy

logging.getLogger("SharedServer")
logging.basicConfig(level = logging.DEBUG,
                    format = "[%(asctime)s] - %(name)s - %(levelname)s: %(message)s",
                    datefmt = "%H:%M:%S"
                    )

shared_dict = {}
class MyDict(object):
    def __init__(self):
        logging.info("Shared dict: " + str(shared_dict))
    
    def get_len(self):
        return len(shared_dict)
    
    def add_key(self, key, val):
        if not shared_dict.has_key(key):
            shared_dict[key] = val
            logging.info("Adding: %s-%s" % (str(key), str(val) ) )
            
    def get_dict(self):
        return shared_dict

class SolverManager(BaseManager): pass
class MyProxy(BaseProxy): pass


class SharedManager(object):
    def __init__(self, addr, auth_key=''):
        self.manager = BaseManager(address=addr, authkey=auth_key)
        self.server = None
    
    def register(self, plugin, clazz, methods):
        self.manager.register(plugin, clazz, exposed=methods)
    
    def get_manager(self):
        return self.manager
    
    def get_server(self):
        return self.server
    
    def start(self):
        try:
            self.server = self.manager.get_server()
            self.server.serve_forever()
        except:
            traceback.print_exc()
    
AUTH_KEY = "'=f_kak2m9mt05om%t9tcv!u%_lj*0brj=$l=w4c^zti1%j^=+o'"
DEFAULT_ADDR = ('127.0.0.1', 50000)

def shared_plugin():
    shared = SharedManager(DEFAULT_ADDR, AUTH_KEY)
    shared.register('solver', MyDict, ['get_len', 'add_key', 'get_dict'])
    
    logging.info("Running server on %s " % str(DEFAULT_ADDR) )
    shared.start()

if __name__ == "__main__":
    shared_plugin()
        
    
