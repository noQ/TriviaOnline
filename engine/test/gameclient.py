import logging
import random
import time
from engine.controller.client import ServerActionHandler
import traceback


logging.getLogger("GameServer - CLIENT :: TCP")
logging.basicConfig(level = logging.DEBUG,
                    format = "[%(asctime)s] - %(name)s - %(levelname)s: %(message)s",
                    datefmt = "%H:%M:%S"                    
                    )

SERVER = "10.100.63.48"
PORT = 11000
if __name__ == "__main__":
    
    session_name = "219d91"
    logging.debug("Session name %s " % session_name)
    
    players = ["5326c3c98d8c7d1674b2589d", "5322f1138d8c7d2bd01b3db9"]
    
    for player_id in players:
        event_data = {
                      "q" : random.randrange(start=0, stop=5),
                      "a" : random.randrange(start=0, stop=3)
                     }
        srv_event_data = {
                            "cmd" : "e",
                            "data" : {
                                    "session" : session_name,
                                    "event" : {
                                        player_id : event_data
                                    }
                            }
                        }
        
        logging.debug("Sending event to server:  %s " % str(srv_event_data))
        
        ''' sending data to server '''
        client = ServerActionHandler((SERVER, PORT))
        client.set_data(srv_event_data)
        client.send()
        try:
            received_data = client.received_data()
        except:
            traceback.print_exc()
            pass        
        # logging.debug("Receiving data from server:  %s " % str(received_data))
        
        time.sleep(2)
    
    