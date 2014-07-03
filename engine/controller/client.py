import logging
import struct
import random
import traceback
import _socket
import gevent
from time import sleep
from gevent import monkey; monkey.patch_socket()
from gevent.pool import Pool
from gevent import socket
from session import GameSession
from rencode import loads, dumps
from engine.controller.rts import ServerCommand

logging.getLogger("GameServer - CLIENT :: TCP")
logging.basicConfig(level = logging.DEBUG,
                    format = "[%(asctime)s] - %(name)s - %(levelname)s: %(message)s",
                    datefmt = "%H:%M:%S"                    
                    )


class Action(object):
    @staticmethod
    def create_session(session, noplayers, player):
        cmd =  {
                  "cmd" : ServerCommand.CREATE_SESSION.value,
                  "data" : {
                            "session" : session.get_name(),
                            "game" : session.game_name,
                            "players" : noplayers,
                            "team" : [str(player.uid)]
                           }
        }
        return cmd

    @staticmethod
    def join_session(session, player):
        cmd = {
                "cmd" : ServerCommand.JOIN_SESSION.value,
                "data" : {
                          "session" : session.get_name(),
                          "player" : player.uid
                        }
               }
        return cmd
    
    @staticmethod
    def destroy(session):
        cmd = {
                "cmd" : ServerCommand.DESTORY_SESSION.value,
                "data" : {
                          "session" : session.get_name()
                        }
                }
        return cmd
    
    @staticmethod
    def check_session(session_name):
        cmd = {
               "cmd" : ServerCommand.CHECK_SESSION.value,
               "data" : {
                          "session" : str(session_name)
                        }
               }
        return cmd

class ServerActionHandler(object):
    
    BUFFER = 1024
    
    def __init__(self, address, debug=True, data=None):
        self.debug = debug
        self.address = address
        self.data = None
        self.received_data = None
        self.socket = socket.socket(type=_socket.SOCK_STREAM)
        
        self.socket.connect(address)
       
    def set_data(self, data):
        self.data = data
        if self.debug:
            logging.info(
                          "Packing data: %s " % str(self.data) 
                          )
            
    def get_reveived_data(self):
        return self.received_data
    
    def send(self):
        if self.debug:
            logging.info(
                          "Sending %s  to %s " % ( len(self.data), str(self.address) )
                          )
        ''' sending data to server '''
        outgoing = dumps(self.data)
        if self.debug:
            logging.info(
                          "Outgoing data: %s " % str(outgoing)
                          )
        self.socket.sendall(outgoing)
            
        ''' receiving data from server '''
        self.received_data = self.socket.recv(self.BUFFER)
        self.received_data = loads(self.received_data)
        if not len(self.received_data):
            if self.debug:
                logging.error("No data received from server.")
                return 
        if self.debug:
            logging.info(
                          "Received data: %s " % str(self.received_data)
                          )

if __name__ == "__main__":
    
    ''' generate session name '''
    game = "Trivia"
    gsession = GameSession()
    session_id = gsession.generate_session_name()
    print "SESSION NAME: ", session_id
    
    ''' ping server '''
    srv_command = { "cmd" : "h" }
    
    ''' create new game session '''
    players_uids = ["xuiy778", "dhjfi98"]    
    srv_create_session = {
                      "cmd" : "c",
                      "data" : {
                                "session" : session_id,
                                "players" : 2,
                                "team" : ["xuiy778" ]
                               }
                      }
    
    ''' join game '''
    srv_join_game = {
                     "cmd" : "j",
                     "data" : {
                               "session" : "45bb7d",
                               "player" : "dhjfi98"
                               }
                     }
    
    srv_destory_game = {
                        "cmd" : "d",
                        "data" : {
                                  "session" : "11d684"
                                  }
                        
                        }
    '''
        for team in teams:
            msg += chr(len(team.name)) + team.name + chr(len(team.users))
            for uid in team.users:
                rt_uid = get_user_real_time_id(users, uid)
                if rt_uid is None:
                    return None
                msg += rt_uid    
    '''
    client = ServerActionHandler(("127.0.0.1", 11000))
    client.set_data(srv_join_game)
    client.send()
    