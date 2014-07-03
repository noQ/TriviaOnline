import datetime
from mongoengine import *
from mongoengine.base import BaseDocument

class Device(EmbeddedDocument):
    ''' store push token '''
    type            = StringField(required=True, default="iOS")
    push_token      = StringField(required=False)
    info            = DictField(required=False, default={})


class UserAccountSettings(Document):
    ''' Keep user account settings '''
    uid         = StringField(required=True, unique=True)
    settings    = DictField(required=False, default={})
    
    meta = {
        'collection': 'account_settings',
        'indexes':  ['uid'],
        'ordering': ['uid'],
    }

class SocialConnector(Document):
    '''
        Store social IDs for connected user based on social connectors:
            - facebook
            - google
            - twitter
            - linkedin
            - instagram
            - tumblr
            
        A social connector looks like this:
            {
                "uid"    : "d95edcdb357ce5...",
                "social" : {
                    "facebook": { "id: : "1228834", "access_token" : "acjwkdfj" },
                    "twitter" : "8888354"
                }
            } 
    '''
    uid             = StringField(required=True, unique=True)
    social          = DictField(required=False, default={})

    meta = {
        'indexes'  : ['uid'],
        'ordering' : ['uid'],
    }


class User(Document):
    '''
        Store information about user
    '''
    uid              = StringField()
    username         = StringField(required=False, default="")
    auth_token       = StringField(required=False, default="")
    password         = StringField(required=False, default="")
    email            = StringField(required=False)
    name             = StringField(required=True)
    first_name       = StringField(required=False)
    last_name        = StringField(required=False)
    avatar           = URLField(required=False, verify_exists=False)
    gender           = StringField(required=False)
    birthday         = StringField(required=False)
    ''' store user device push token '''
    devices          = SortedListField(EmbeddedDocumentField(Device, required=False), default=[])
    ''' store social connector '''
    social_connector = ReferenceField(SocialConnector, required=False, reverse_delete_rule=CASCADE)
    '''
        where user living (e.g Romania ) - from Facebook if possible
    '''
    country          = StringField(required=False)
    city             = StringField(required=False)
    '''
        The user's locale. `string` containing the ISO Language Code and ISO Country Code.
    '''
    locale           = StringField(required=False)
    ''' user quote '''
    about_me         = StringField(required=False)
    ''' user ranking and rankig title '''
    title             = StringField(required=True, default='Beginner')
    ranking           = IntField(required=False, default=0)
    '''
       The user's timezone offset from UTC. Available only for the current user. 
       Note: not implemented!
    '''
    timezone          = IntField(required=False)
    created_time      = DateTimeField(default=datetime.datetime.now)
    '''
        The last time the user's profile was accessed 
    '''
    last_login_time   = DateTimeField(required=True)
    ''' check if account is active '''
    is_active         = BooleanField(default=True, required=False)
    ''' account version '''
    version           = IntField(required=True, default=1)
    
    meta = {
        'indexes':  ['uid', 'username', 'name', 'email'],
        'ordering': ['uid','email'],
    }
    
    def __str__(self):
        return str(self.email)

    def get_full_name(self):
        """Returns the users first and last names, separated by a space.
        """
        full_name = '%s %s' % (self.first_name or '', self.last_name or '')
        return full_name.strip()

    
class Player(EmbeddedDocument):
    info_attrs = ("name", "title", "ranking", "avatar", "country", "city")
    
    """ Define player """
    uid      = StringField(required=True)
    ''' player status like: 'ready to play', 'disconnected', 'win', 'loose' '''
    status   = IntField(required=False)
    ''' other inform about player (team name, full name, title, city, country, avatar etc '''
    info = DictField(required=False)

    def get_player_info(self, user):
        info = {}
        for attr in self.info_attrs:
            if hasattr(user, attr):
                info[attr] = getattr(user, attr)
        self.info = info
        return info

class BotPlayer(DynamicDocument):
    """
        Define properties for bot player
    """
    uid       = SequenceField()
    name      = StringField(required=True)
    ranking   = IntField(required=True, default=1)
    
    is_active = BooleanField(default=True, required=False)
    props     = DictField(required=False)

    def __str__(self):
        return str(self.name)
    
    def get_properties(self):
        return self.props


class Session(DynamicDocument):
    ''' session name '''
    name        = StringField(required=True)
    ''' session owner UID '''
    owner_uid   = StringField(required=True)
    ''' create session for game name '''
    game_name   = StringField()
    ''' define game type: single player, multiplayer, 2 vs. 2 etc '''
    game_type   = StringField(required=False)
    ''' embeded document to keep all users connected in this session '''
    players     = SortedListField(EmbeddedDocumentField(Player), required=False)
    ''' slots '''
    slots       = IntField(required=True, min_value=0)
    ''' available slots '''
    available_slots = IntField(required=True, min_value=0)
    ''' session status: in_use, expired etc '''
    status      =  IntField(required=False, min_value=0, max_value=5 )
    ''' real time server location '''
    rtserver    = DictField(required=False, default={})
    ''' when session is created '''
    created_at  = DateTimeField(default=datetime.datetime.now)
    ''' when session expire ''' 
    expired_at  = IntField(required=True)
    ''' flag that mark if session is active or not '''
    is_active   = BooleanField(required=False)
    ''' keep other info about game and session '''
    info        = DictField(required=False, default={})
    
    meta = {
        'collection': 'sessions',
        'indexes'  : ['name', ],
        'ordering' : ['name']
    }
    
    def __str__(self):
        """
            return session name : 7663@u8948384
        """
        return "%s@%s" % (self.name, self.owner_uid)

class LeaderboardType(Document):
    typeid    = SequenceField()
    name      = StringField(required=True)
    is_active = BooleanField(default=True)

    meta = {
        'collection' : 'leaderboard_type',
        'indexes':  ['typeid', 'name'],
        'ordering': ['name'],
    }
    
    def get_name(self):
        return self.name
    
    def __unicode__(self):
        return str(self.type)


class Leaderboard(DynamicDocument):
    uid        = StringField(required=True)
    full_name  = StringField(required=True)
    ''' define leaderboard type '''
    kind       = ReferenceField('LeaderboardType')
    score      = IntField(default=0)
    properties = DictField() 
    
    meta = {
        'collection' : 'leaderboard',
        'indexes':  ['uid'],
        'ordering': ['-score'],
    }
    
    def __str__(self):
        return str(self.uid)

class GameType(Document):
    """
        Define game type: single, challange, online, play with friends etc
    """
    typeid      = SequenceField()
    name        = StringField(verbose_name='Game Type')
    info        = DictField()
    is_active   = BooleanField(default=True)

    meta = {
        'collection' : 'game_type',
        'ordering': ['name'],
    }

    def __str__(self):
        return str(self.name)

class Score(BaseDocument):
    """
        Keep user score
    """
    uid         = StringField(required=True)
    game_type   = ReferenceField('GameType')
    score       = FloatField()
    
    meta = {
            "_is_document" : False
            }

class UserStats(DynamicDocument):
    uid     = StringField(verbose_name='User ID')
    played  = IntField(default=0, verbose_name='Total Games Played')
    wind    = IntField(default=0, verbose_name='Win games')
    loose   = IntField(default=0, verbose_name='Looses games')
    draw    = IntField(default=0, verbose_name='Draw games')
        
    meta = {
        'collection' : 'user_stats',
        'indexes':  ['uid'],
        'ordering': ['uid'],
    }
    
    def __str__(self):
        return str(self.uid)
    

class Category(Document):
    ''' define short id '''
    catid       = SequenceField(required=True)
    name        = StringField(verbose_name='Category Name')
    active      = BooleanField(default=True)

    meta = {
        'collection' : 'categories',
        'index' : ['catid'],
        'ordering': ['name'],
    }
    
    def __str__(self):
        return self.name

class Reward(DynamicDocument):
    name    = StringField(verbose_name='Reward Name')
    xp      = IntField(default=0, verbose_name='Experience')
    coins   = IntField(default=0, verbose_name='Coins')
    other   = DictField(verbose_name='Others rewards')
    ''' apply this reward for story '''
    by_story = BooleanField(default=False)
    ''' apply this reward for mission '''
    by_mission = BooleanField(default=False)
    ''' apply this reward when user level is incrased '''
    by_levelup = BooleanField(default=False)
    is_active = BooleanField(default=True)

    meta = {
        'collection' : 'rewards',
        'ordering': ['name'],
    }

    def __str__(self):
        return str(self.level)

class UserRank(Document):
    ranking  = IntField()
    points = IntField(verbose_name='Max. points to reach the level')

    meta = {
        'collection' : 'user_rank',
        'ordering': ['ranking'],
    }

    def __unicode__(self):
        return "%s/%s" % ( str(self.ranking), str(self.points) )
    
    def get(self, ranking):
        ranking = UserRank.objects(ranking=ranking).first()
        if ranking is None:
            return None
        return ranking
        
    
    @staticmethod
    def check_ranking(points):
        current_lvl, next_lvl = None, None
        
        rankings = UserRank.objects
        cnt = rankings.count()
        if cnt > 0:
            for l in xrange(cnt):
                current_lvl = rankings[l]
                next = l + 1
                if next > cnt:
                    next_lvl = current_lvl
                else:
                    next_lvl = rankings[next]
                if points <= next_lvl.points:
                    break
        return  current_lvl, next_lvl
 
class Story(Document):
    """ Define story """
    name            = StringField(verbose_name='Story Name')
    ''' get reward if user finnish the story '''
    rewards         = ReferenceField('Reward')
    ''' unlock story at level '''
    unlock_at_level = IntField(default=0)
    is_active       = BooleanField(default=True)

    meta = {
        'collection' : 'story',
        'ordering': ['name'],
    }

    def __str__(self):
        return str(self.name)

class Mission(BaseDocument):
    """ Define missions """
    name        = StringField(verbose_name='Mission name')
    ''' mission cover '''
    cover       = URLField(verify_exists=False)
    properties  = DictField()
    reward      = ReferenceField('Reward')
    is_active   = BooleanField(default=True)

    meta = {"_is_document" : False}
    
    def __str__(self):
        return str(self.name)

class StoryMission(Document):
    """ Define missions for story  """
    name        = StringField(verbose_name='Story Name')
    ''' mission cover '''
    cover       = URLField(verify_exists=False)
    ''' story name '''
    story       = ReferenceField('Story')
    ''' define missions for story '''
    missions    = ListField(ReferenceField('Mission'))
    ''' define rewards if user wins the story '''
    rewards     = ReferenceField('Reward')
    ''' define story properties '''
    properties  = DictField()
    is_active   = BooleanField(default=True)

    meta = {
        'collection' : 'story_mission',
        'ordering': ['name'],
    }

    def __str__(self):
        return str(self.name)

    