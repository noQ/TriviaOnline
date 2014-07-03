import inspect
import logging
import os
import sys
import time
import traceback
import signal
import glob
from enum import Enum
import gevent 
from gevent import monkey; monkey.patch_socket()
from gevent.server import StreamServer
from rencode import dumps, loads
from threading import Lock
from gevent.socket import socket

logging.getLogger("GameServer :: TCP")
logging.basicConfig(level = logging.DEBUG,
                    format = "[%(asctime)s] - %(name)s - %(levelname)s: %(message)s",
                    datefmt = "%H:%M:%S"                    
                    )


class ControllerPlugin:
    def __init__(self):
        self.session = None
        self.score = None
    
    def play(self):
        raise NotImplementedError("Please implement me!")
    
    def stop(self):
        raise NotImplementedError("Please implement me!")
    
    def pause(self):
        raise NotImplementedError("Please implement me!")
    
    def game_logic(self):
        raise NotImplementedError("Please implement me!")
    
    def get_server_info(self):
        raise NotImplementedError("Please implement me!")


BUFFER = 1024
"""
    PLUGINS = Dictionary that store all the available plugins
"""

PLUGINS = {}
PLUGIN_METHODS = {}
PLUGIN_METHODS_MAP = {}


def clazz_inspector(clazz):
    methods = inspect.getmembers(clazz, inspect.ismethod)
    methods_map = {}
    for method in methods:
        methods_map[method[0]]=method[1]
    return methods_map  
    
def load_plugins(plugin_path):
    global PLUGINS
    ''' define plugin path '''
    plugin_handler = PluginHandler(plugin_path)
    plugin_handler.load_plugins()
    for game, game_module in PLUGINS.items():
        PLUGIN_METHODS[game] = inspect.getmembers(game_module.__class__ , inspect.ismethod)
        PLUGIN_METHODS_MAP[game] = clazz_inspector(game_module.__class__)
    return PLUGINS

class PluginHandler(object):
    """
        Plugin loader
    """
    PY_EXT          = ".py"
    ALL_PY_FILES    = "*.py"
    ALL_PYC_FILES   = "*.pyc"    
    
    def __init__(self, path, logdata = False):
        self.plugin_path = path
        self.logdata = logdata
        
        if self.logdata:
            logging.info("Start plugin handler")
    
    @staticmethod
    def get_plugin(name):
        if PLUGINS.has_key(name):
            logging.info("Loading plugin %s " % str(name))
            return PLUGINS.get(name)
        return None
            
    @staticmethod
    def get_from_dict(plugin_dict, name):
        if plugin_dict.has_key(name):
            logging.info("Loading plugin %s " % str(name))
            return plugin_dict.get(name)
        return None        
    
    def load_plugin(self, clazz_name):
        clazz = __import__(clazz_name)
        PLUGINS[clazz_name] = getattr(clazz, clazz_name)()
        return PLUGINS[clazz_name]
    
    def reload_plugin(self,clazz_name):
        if self.is_loaded(clazz_name):
            clazz = reload(sys.modules[clazz_name])
            PLUGINS[clazz_name] = getattr(clazz, clazz_name)()
            return PLUGINS[clazz_name]
        else:
            return self.load_plugin(clazz_name)
    
    def remove_plugin(self,clazz_name):
        if self.is_loaded(clazz_name):
            try:
                del PLUGINS[clazz_name]
                del sys.modules[clazz_name]
            except KeyError:
                traceback.print_exc()
    
    def clean_plugin_folder(self):
        _path = self.plugin_path + "/" + PluginHandler.ALL_PYC_FILES
        _pyc_files = glob.glob(_path)
    
    def is_loaded(self,clazz_name):
        if PLUGINS.has_key(clazz_name):
            return True
        return False
    
    def is_py_file(self,filename):
        if filename.endswith(PluginHandler.PY_EXT):
            return True
        return False
    
    def __whatis(self, event):
        what = 'directory' if event.is_directory else 'file'
        return what

    def get_class_name(self, src_path):
        plugin_name = os.path.basename(src_path)                
        clazz_name, ext = os.path.splitext(plugin_name)
        return clazz_name

    def load_plugins(self):
        ''' Called when handler is initialized '''
        sys.path.append(self.plugin_path)
        _path = self.plugin_path + "/" + PluginHandler.ALL_PY_FILES
        _plugins = glob.glob(_path)
        if len(_plugins) > 0:
            for plugin in _plugins:
                plugin_name = os.path.basename(plugin)                
                if plugin_name != "__init__.py": 
                    try:
                        if self.is_py_file(plugin_name):
                            clazz_name, ext = os.path.splitext(plugin_name)
                            if not self.is_loaded(clazz_name):
                                if self.logdata:
                                    logging.info("Class not in cache.Try to load clazz")
                                ''' load clazz '''
                                self.load_plugin(clazz_name)
                                if self.logdata:
                                    logging.info("Plugin %s loaded", str(plugin_name))
                    except Exception as exc:
                        traceback.print_exc()
                        if self.logdata:
                            logging.info("Unable to load plugin : " + str(exc))        
        return PLUGINS


"""
    SESSIONS = Dictionary that stores active sessions
    keeps all sessions in memory like:
    SESSIONS = {
                "xvf67u" : { }
                ...
                ... 
               }
"""
SESSIONS = {}
class RTSSession(object):
    def __init__(self, id, game, players, team, properties={}):
        self.id = id
        self.game = game
        if players is None:
            players = 0
        self.players = players
        if team is None:
            team = []
        self.team =  team
        self.props = properties
        self.lastrequest = time.time()
        self._score = {}
    
    @property
    def score(self):
        return self._score
    
    @score.setter
    def score(self, score):
        self._score = score

    def properties(self):
        return self.props
    
    def set_properties(self, properties):
        self.props = properties 
    
    def get_players(self):
        return self.players
    
    def player_exists(self, player_id):
        if player_id in self.team:
            return True
        return False
    
    def add_player(self, player_id):
        if len(self.team) >= self.players:
            return False
        if player_id in self.team:
            return False
        self.team.append(player_id)
        return True
        

class SessionFactory(object):
    SESSION_KEY = "session"
    GAME_KEY    = "game"
    PLAYERS_KEY = "players"
    PLAYER_KEY  = "player"
    TEAM_KEY    = "team"
    PROPERTIES  = "props"
    EVENT_KEY   = "event"
    
    def __init__(self):
        self.lock = Lock()
    
    def get(self, session_id):
        ''' get session by id '''
        self.lock.acquire()
        if not self._exist(session_id):
            return None
        session = SESSIONS[session_id]
        self.lock.release()
        return session
    
    def update(self, session_id, session):
        self.lock.acquire()
        SESSIONS[session_id] = session
        self.lock.release()
    
    def _exist(self, session_id):
        if SESSIONS.has_key(session_id):
            return True
        return False
    
    def get_key(self, data, key):
        if not data.has_key(key):
            return None
        return data.get(key)
    
    def destroy(self, session_id):
        self.lock.acquire()
        is_deleted = False
        try:
            del SESSIONS[session_id]
            is_deleted = True
        except KeyError:
            pass
        self.lock.release()
        return is_deleted
    
    def populate(self, data):
        logging.info("Retriving data: %s " % str(data))
        
        if not isinstance(data, dict):
            return False
        
        is_populated = False
        self.lock.acquire()        
        try:
            _id = self.get_key(data, self.SESSION_KEY)
            if self._exist(_id):
                is_populated = False
            else:
                ''' extract data from dict '''
                game_name = self.get_key(data, self.GAME_KEY)
                logging.info("Game name: %s " % str(game_name))
                if game_name is None:
                    is_populated = False
                else:
                    ''' get plugin by name '''
                    game = PluginHandler.get_plugin(game_name)
                    players = self.get_key(data, self.PLAYERS_KEY)
                    properties = self.get_key(data, self.PROPERTIES)
                    team = self.get_key(data, self.TEAM_KEY)
                    ''' update session '''
                    SESSIONS[_id] = RTSSession(_id,
                                               game,
                                               players,
                                               team,
                                               properties
                                           )
                    is_populated = True
        finally:
            self.lock.release()
        return is_populated

class ServerCommand(Enum):
    ''' ping server command '''
    PING            = "p"
    ''' server is alive ? '''
    HEART_BEAT      = "h"
    ''' create session '''
    CREATE_SESSION  = "c"
    ''' join session '''
    JOIN_SESSION    = "j"
    ''' create event '''
    EVENT           = "e"
    ''' destroy session '''
    DESTORY_SESSION = "d"
    ''' check session '''
    CHECK_SESSION   = "s"
    
    SUCCESS = "OK"
    NOT_OK  = "NOK"
    FAILED  = "FAILED"
    NO_DATA = "NODATA"


class RequestParser:
    """
        Extract data from requests
        - data must be an instance of dict:
            Example:
             {
                "cmd" : "c",
                "data" : {
                          "session" : "xfvg",
                          "players" : 2,
                          "team" : ["xuiy778", "dhjfi98"],
                          }
             }
             
             - where:
                     cmd  - server command:
                               c - create game
                               h - join game
                               e - event in game
                               h - heart beat
                               p - ping server
                     data - contain user data like session ID, players, team 
                         session - is game session ID used by the server during the game
                         players - total numbers of players in game
                         team    - team IDs (array)
                         
            Client example:
            
                client = TCPClient(("127.0.0.1", 11000))
                session_id = gsession.generate_session_name()
                players_uids = ["xuiy778", "dhjfi98"]
                srv_create_session = {
                          "cmd" : "c",
                          "data" : {
                                    "session" : session_id,
                                    "players" : ["xuiy778", "dhjfi98"],
                                   }
                          }
                client.set_data(srv_create_session)
                client.send()            
    """
    DATA_KEY = "data"
    CMD_KEY = "cmd"
    
    def __init__(self, request):
        self.request = request
        self.srv_command = None
        self.srv_data    = None
    
    def get_data(self):
        self.request = loads(self.request)
        if not self.has_command():
            return None, 
        if self.request.has_key(self.DATA_KEY):
            self.srv_data = self.request.get(self.DATA_KEY)
        return self.srv_command, self.srv_data
        
    def has_command(self):
        if not self.request.has_key(self.CMD_KEY):
            return False
        self.srv_command = self.request.get(self.CMD_KEY)
        if self.srv_command is None:
            return False
        return True
            
sessionFactory = SessionFactory()
class ClientProcessor(object):
    """
        Process all data from client
            - Mandatory parameters:
                - "cmd"  - command
                - "data" - user data (dict)
                
            - Server commands:
                - Create new session: "c"
                    - Request example:
                         {
                          "cmd" : "c",
                          "data" : {
                                    "session" : "11d684",
                                    "players" : 2,
                                    "team" : ["xuiy778" ]
                                   }
                         }
                    
                - Join player in session: "j"
                    - Request example:
                        {
                         "cmd" : "j",
                         "data" : {
                                   "session" : "11d684",
                                   "player" : "dhjfi98"
                                   }
                         }
                         
                - Game event : "e"
                    - Request example:
                        {
                            "cmd" : "e",
                            "data" : {
                                    "session" : 11d684,
                                    "event" : {
                                        ...
                                        ...
                                        ...
                                    }
                            }
                        }
                
                - Destory session: "d"
                    - Request example:
                        {
                        "cmd" : "d",
                        "data" : {
                                  "session" : "11d684"
                                  }
                        }
 
    """
    def __init__(self, socket, addr, data=None, debug=False):
        self.socket = socket
        self.address = addr
        self.session = None
        self.uid = None
        self.data = data
        self.lastrequest = time.time()
        self.server_packet_cnt = 1
        self.debug = debug
    
    def set_session(self, session):
        self.session = session
    
    def read_request(self):
        try:
            self.data = self.socket.recv(BUFFER)
        except TypeError:
            logging.error("Data type is not valid!")
        """ read requests from client """
        if not len(self.data):
            ''' if no data then send failed response to client '''
            self.send(ServerCommand.FAILED)
        if self.session:
            ''' set session time '''
            self.lastrequest = time.time()
        ''' parse data from client. extract server command and data '''
        srv_command, self.data = RequestParser(self.data).get_data()
        if self.debug:
            logging.error(
                          "Receiving data from %s: ( %s : %s) " % (self.address, srv_command, str(self.data))
                          )
        ''' check server commands '''
        if srv_command in ( ServerCommand.PING.value,
                            ServerCommand.HEART_BEAT.value):
            self.send(
                      ServerCommand.SUCCESS.value
                      )
        elif srv_command == ServerCommand.CREATE_SESSION.value:
            ''' create new game session. all sessions are stored in memory '''
            populated = sessionFactory.populate(self.data)
            if populated:
                command = ServerCommand.SUCCESS.value
            else:
                command = ServerCommand.FAILED.value
            self.send(command)
            
        elif srv_command == ServerCommand.JOIN_SESSION.value:
            """ join player in session """
            
            command = ServerCommand.FAILED.value
            
            ''' join player in session '''
            if not self.data and type(self.data) is not dict:
                command = ServerCommand.NO_DATA.value
            else:
                ''' extract session from request '''
                session_id = sessionFactory.get_key(self.data, sessionFactory.SESSION_KEY)
                if session_id:
                    ''' get session if exist '''
                    session = sessionFactory.get(session_id)
                    if session:
                        ''' set player in session '''
                        player_id = sessionFactory.get_key(self.data, sessionFactory.PLAYER_KEY)
                        if player_id:
                            ''' check if player exists in session '''
                            if session.player_exists(player_id):
                                command = ServerCommand.SUCCESS.value
                            else:
                                ''' add player in session '''
                                is_added = session.add_player(player_id)
                                ''' if True then update current session '''
                                if is_added:
                                    ''' update session '''
                                    sessionFactory.update(session_id, session)
                                    ''' set server command: success '''
                                    command = ServerCommand.SUCCESS.value
                            
            self.send(command)
        elif srv_command == ServerCommand.EVENT.value:
            """
                {
                    "cmd" : "e",
                    "data" : {
                            "session" : 11d684,
                            "event" : {
                                ...
                                ...
                                ...
                            }
                    }
                }            
            """
            if not self.data and type(self.data) is not dict:
                command = ServerCommand.NO_DATA.value
            else:
                has_event = True
                try:
                    event_data = self.data.get("event")
                except KeyError:
                    has_event = False
                    command = ServerCommand.FAILED.value
                
                if has_event:
                    session_id = sessionFactory.get_key(self.data, sessionFactory.SESSION_KEY)
                    if session_id:                    
                        session = sessionFactory.get(session_id)
                        if session is None:
                            command = ServerCommand.FAILED.value
                        else:
                            if DEBUG_MODE:
                                logging.debug("Session data: %s " % str(session))
                                logging.debug("Event data: %s " % str(event_data))
                                
                            session.set_properties(event_data)
                            sessionFactory.update(session_id, session)
                            ''' get session properties '''
                            command = session.properties()
                            print "new command: ", str(command)
            self.send(
                      command
                      )
            
        elif srv_command == ServerCommand.CHECK_SESSION.value:
            ''' check if session exists on RT server '''
            has_data = True
            if not self.data and type(self.data) is not dict:
                command = ServerCommand.NO_DATA.value
                has_data = False
            
            if has_data:
                session_id = sessionFactory.get_key(self.data, sessionFactory.SESSION_KEY)
                if session_id:
                    command = ServerCommand.SUCCESS.value
                else:
                    command = ServerCommand.FAILED.value
            self.send(
                      command
                      )
                
        elif srv_command == ServerCommand.DESTORY_SESSION.value:
            """ destroy  game session """
            has_data = True
            if not self.data and type(self.data) is not dict:
                command = ServerCommand.NO_DATA.value
                has_data = False
                
            if has_data:
                session_id = sessionFactory.get_key(self.data, sessionFactory.SESSION_KEY)
                if session_id:
                    ''' get session if exist '''
                    session = sessionFactory.get(session_id)
                    if session:
                        ''' destroy session from memory '''
                        sessionFactory.destroy(session_id)
                        command = ServerCommand.SUCCESS.value
                    
            self.send(
                      command
                      )
        else:
            self.send(ServerCommand.NO_DATA.value)
    
    def pack_data(self, packet):
        return dumps(packet)
      
    def send(self, packet):
        if packet is None:
            packet = self.pack_data(ServerCommand.NOT_OK.value)
        else:
            packet = self.pack_data(packet)
        print packet
        self.socket.sendall(packet)

class GameServer(StreamServer):
    """
        Game Server
    """
    BUFFER = 1024
    
    def __init__(self, *args, **kwargs):
        StreamServer.__init__(self, *args, **kwargs)
        self.server_address, self.port = None, None
        if kwargs.has_key("server_address"):
            server_address = kwargs.get("server_address")
            if isinstance(server_address, tuple):
                self.server_address = server_address[0]
                self.port = server_address[1]
        
        self.max_pool = None
        if kwargs.has_key("max_pool"):
            self.pool = kwargs.get("max_pool")
        
        self.debug = False
        self.server_packet_cnt = 1
        self.enable_signals()
    
    def process_command(self, client):
        socket, address = client
        try:
            processor = ClientProcessor(socket, address, debug=self.debug)
            processor.read_request()
        except (ValueError, TypeError) as exc:
            logging.error(exc)
        except Exception as exc:
            logging.error(exc)
            socket.close()
    
    def session_checker(self, client):
        print self.processor
    
    def handle(self, socket, address):
        client = (socket, address)
        gevent.spawn(self.process_command, client)
              
    def enable_signals(self):
        gevent.signal(signal.SIGTERM, self.exit)
        gevent.signal(signal.SIGINT, self.exit)
    
    def run(self, serve_forever=True):
        if not serve_forever:
            self.start()
        else:
            self.serve_forever()
    
    def exit(self):
        if self.debug:
            logging.error("Signal detected! Server is shutting down...")            
        self.stop()
        sys.exit(0)
    
    def debug_mode(self, mode=False):
        self.debug = mode

BIND_IP = "0.0.0.0"
BIND_PORT = 11000
DEBUG_MODE = True
PLUGIN_PATH = "/var/www/trivia/plugins/"
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    sys.path.append(CURRENT_PATH)
    logging.info("Server current path: %s " % str(CURRENT_PATH) )
    try:
        logging.info("Loading plugins")
        load_plugins(PLUGIN_PATH)
    except Exception as exc:
        logging.error("Unable to run game plugins. The reason is : %s" % str(exc))        
        traceback.print_exc()
    
    logging.info("Running server on %s:%d " % (BIND_IP, BIND_PORT) )
    try:
        ''' run server '''
        game_srv = GameServer((BIND_IP, BIND_PORT))
        
        game_srv.debug_mode(DEBUG_MODE)
        game_srv.run(serve_forever=True)
    except KeyboardInterrupt:
        pass
