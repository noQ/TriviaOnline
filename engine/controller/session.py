import time
import uuid
import itertools
import random
from enum import IntEnum
from memory_profiler import profile
from django.core.cache import cache
from engine.models import Session, Player

class PlayerStatus(IntEnum):
    ''' Define different statuses for player '''
    available     = 0
    not_available = 1
    not_ready     = 2
    ready_to_play = 3
    busy          = 4


class OnlineChecker(object):
    """
        - used to check if player is online or not
        - set user status (available, not available, busy, etc)
        - get total numbers of online players but not exclude players with status busy, playing
        - return a list with all available players
    """
    ONLINE_CACHE_KEY = "online_users"
    COUNT_ONLINE = "cnt_online_users"
    MAX_SIZE     = 100
    
    def __init__(self, uid=None):
        ''' define user id '''
        self.uid = uid
        ''' store cache dict '''
        self.cache_data = self.get_or_create_key()
        self.count_users = 0
    
    def set_uid(self, uid):
        self.uid = uid
    
    def get_or_create_key(self, key=ONLINE_CACHE_KEY, data_type={}):
        """ get or create key in cache.
            in this key we keep all online users 
        """
        cache_data = cache.get(key)
        if cache_data is None:
            ''' create new key if not exists '''
            cache.set(key, data_type)
            cache_data = cache.get(key)
        return cache_data
    
    def player_exists(self):
        ''' check if user exist in dict '''
        if self.uid is None:
            raise TypeError
        ''' check if user is in list '''
        if self.cache_data.has_key(self.uid):
            return True
        return False
    
    def count_players(self):
        """ return total no. of users online """
        return self.get_or_create_key(key=self.COUNT_ONLINE, data_type=0)
    
    def set_status(self, status):
        ''' set user status '''
        self.cache_data[self.uid] = status
        cache.set(self.ONLINE_CACHE_KEY, self.cache_data)
    
    def is_available(self):
        ''' user is available to play '''
        self.set_status(PlayerStatus.available.value)
        ''' increment online users '''
        self.count_players()
        cache.incr(self.COUNT_ONLINE)
    
    def not_available(self):
        ''' user exist from game '''
        self.set_status(PlayerStatus.not_available.value)
        ''' decrement online users '''
        self.count_players()
        cache.decr(self.COUNT_ONLINE)
    
    def _random_players(self, number):
        keys = random.sample(self.cache_data.keys(), number)
        players_list = dict()
        for k in keys:
            if self.cache_data.has_key(k):
                players_list[k] = self.cache_data.get(k)
        return players_list
        

    def get_players_by_status(self, status, max_list=10, random_order=True):
        if len(self.cache_data) == 0:
            return 0, []
        if max_list > len(self.cache_data) or max_list > self.MAX_SIZE:
            players_list = self.cache_data
        ''' return a list with last X online players '''
        if random_order:
            ''' return players in random order if True '''
            if max_list > len(self.cache_data):
                players_list = self.cache_data
            else:
                players_list = self._random_players(max_list)
        else:
            ''' return first X players from list '''
            players_list = dict(
                                itertools.islice(self.cache_data.iteritems(), 0, max_list) 
                                )
        ''' extraxt players by status '''
        players = [key for key, val in players_list.iteritems() if val == status]
        ''' return total players and list of players '''
        return (len(players), players)
    
    def get_available_players(self, **kwargs):
        """ shortcut to get all available players """
        return self.get_players_by_status(PlayerStatus.available.value, **kwargs)
    

class SessionStatus(IntEnum):
    ''' Define different statuses for game session '''
    incomplete = 1
    ready_to_play = 2
    finnish  = 3
    inactive = 4
    
class GameSession(object):
    """
        Create new game session in cache
    """
    SESSION_NAME_SIZE = 6
    DEFAULT_SLOTS = 2
    ''' session persist in cache 2 minutes ''' 
    DEFAULT_TTL_SESSION = 60 * 2 
    
    def __init__(self, name=None, user=None, slots=None, name_size=6, auto_pickup=True):
        self.session_name = name
        self.session = None
        self.user = user
        ''' auto pickup user from available users '''
        self.auto_pickup = auto_pickup
        self.name_size = name_size
        if self.name_size == 0:
            self.name_size = self.SESSION_NAME_SIZE
        ''' define slots (players) for current session
            default are two players on game
        '''
        self.slots = self.DEFAULT_SLOTS if slots is None else slots
        self.game_name = None

    def set_user(self, user):
        ''' set session user '''
        self.user = user
    
    def get_name(self):
        """ returns session name """
        return self.session_name
    
    def set_game_name(self, name):
        """ set game name """
        self.game_name = name

    def generate_session_name(self):
        ''' generate random session name '''
        unique_id = uuid.uuid4()
        self.session_name = unique_id.hex[:self.name_size]
        return self.session_name
        
    def get_session(self):
        return self.session
    
    def expire_in(self, seconds=DEFAULT_TTL_SESSION):    
        """ 
            return a UNIX style timestamp representing +X min from now
            used to set expiration time for current session 
        """
        return int(time.time() + seconds)    
    
    def is_expired(self, session_time):
        """
            check if session is expired
        """
        if int(time.time()) > session_time:
            return True
        return False
        
    
    def has_free_slots(self):
        """ check if session has enough space to add new player """
        if self.session.available_slots == 0:
            return False
        return True
    
    def get_available_slots(self):
        return self.session.available_slots
    
    def find_session(self, name=None):
        """ find session by name.
            this method must be used to check duplicate sessions 
        """
        if not any( (name, self.session_name) ):
            raise TypeError("session name and parameter 'name' has null values")
        
        ''' return session name '''
        session = self.session_name if name is None else name
        ''' looking for session '''
        session_data = Session.objects(name=session, is_active=True).first()
        if session_data is None:
            return False
        self.session = session_data
        return True
    
    def get_awaiting_sessions(self):
        """ Get user session """
        if self.user is None:
            raise TypeError("USER object must be provided!")
        self.session = Session.objects(players__uid=self.user.uid).first()
        if self.session is not None:
            self.session_name = self.session.name
        return self.session
    
    def create(self):
        """
            Create new session. default status is 'incomplete'
        """
        if self.user is None:
            raise TypeError("USER object must be provided!")
        
        ''' generate random name if not provided '''
        while not self.find_session(self.generate_session_name()):
            """ create new session with one player and status 'free' """
            player = Player(uid = self.user.uid,
                            status = PlayerStatus.ready_to_play.value
                            )
            ''' get player info based on current user '''
            player.get_player_info(self.user)
            ''' set available slots '''
            self.slots -= 1
            ''' create session object '''
            self.session = Session(name = self.session_name,
                                   owner_uid = self.user.uid,
                                   status = SessionStatus.incomplete.value,
                                   is_active = True,
                                   expired_at = self.expire_in(),
                                   players = [player],
                                   slots = self.slots,
                                   game_name = self.game_name,
                                   available_slots = self.slots
                              )
            self.session.save()
            return self.session
        return None
    
    def destroy(self, name=None):
        """
            delete session from cache
        """
        if self.find_session(name):
            self.session.delete()
    
    def can_join(self, user=None):
        """
            Join in session with different status: ready to play, not ready etc.
             
        """
        if not self.has_free_slots():
            return False
        if user is not None:
            self.set_user(user)
        ''' decrement slots '''
        self.session.available_slots -= 1
        """ check again if session has free slots. 
            if no slots available then change session status to "ready to play" (game),
            and set the player
        """ 
        if not self.has_free_slots():
            self.session.status = SessionStatus.ready_to_play.value
        
        player_status = PlayerStatus.not_ready.value
        if self.session.status == SessionStatus.ready_to_play.value:
            player_status = PlayerStatus.ready_to_play.value
        ''' create player object '''
        player = Player(uid = self.user.uid,
                        status = player_status
                        )
        ''' set player additional info '''
        player.get_player_info(self.user)
        ''' add player to current session '''
        self.add_player(player)
        ''' save session '''
        self.session.save()
        return True

    def add_player(self, player):
        """ add new player in session """
        if self.session:
            if not hasattr(self.session, "players"):
                self.session.players = []
            else:
                if not isinstance(self.session.players, list):
                    raise TypeError("Not instace of list!")
            self.session.players.append(player)

    def get_players(self):
        """ get players session """
        if self.session:
            if hasattr(self.session, "players"):
                players = [p._data for p in self.session.players]
                return dict(name = self.session.name,
                            status = self.session.status, 
                            players = players,
                            slots = self.session.available_slots,
                            rtserver= self.session.rtserver
                            )
        return None
            
    def set_player_status(self, uid, status):
        """ set player status """
        if not hasattr(self.session, "players"):
            return None
        if len(self.session.players) > 0:
            for player in self.session.players:
                if player.uid == uid:
                    player.status = status
                    break
        return self.session.players
            
    def has_game_logic(self):
        if not hasattr(self.session, "game_logic"):
            return None
        return getattr(self.session, "game_logic")
    
    def set_game_logic(self, logic_data):
        setattr(self.session, "game_logic", logic_data)
        self.session.save()


def test_online_checker():
    from engine.util.auth import AuthToken
    token = AuthToken()
    
    uids = [] 
    for i in xrange(1000):
        uids.append(token.generate_auth_token())
    """ put all tokens in cache """
    checker = OnlineChecker()
    total_players = checker.count_players()
    if total_players < 100:
        for uid in uids:
            checker.set_uid(uid)
            checker.is_available()
    
    print "total players", total_players
    players = checker.get_available_players(random_order=True)
    print "get total available players: ",  players

def test_available_players():
    checker = OnlineChecker()
    players = checker.get_available_players(random_order=True)
    print "get total available players: ",  players
    

if __name__ == "__main__":
    test_online_checker()
    
    
    
    
    
    
    
    
    
        