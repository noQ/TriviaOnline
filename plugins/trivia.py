import random
import logging
try:
    from rts import ControllerPlugin
except:
    from engine.controller.rts import ControllerPlugin

logging.getLogger("Plugin")
logging.basicConfig(level = logging.DEBUG,
                    format = "[%(asctime)s] - %(name)s - %(levelname)s: %(message)s",
                    datefmt = "%H:%M:%S"                    
                    )

class trivia(ControllerPlugin):
    
    def __init__(self, **kwargs):
        plugin_name = self.__class__.__name__
        logging.info("Loading plugin: %s " % str(plugin_name))
        
    def play(self):
        print "Playing game"
    
    def stop(self):
        print "Stop game"
    
    def pause(self):
        print "Pause game"
    
    def game_logic(self):
        """ This will be the game logic """
        from game.views import get_all_questions
        questions = get_all_questions()
        random_questions = random.sample(questions.values(), 10)
        if len(random_questions) == 0:
            random_questions = {}    
        return random_questions
    
    def get_server_info(self):
        self.server_name = "10.100.63.48"
        self.server_port = 11000
        
        return dict(
                    server=self.server_name,
                    port=self.server_port
                    )
        
