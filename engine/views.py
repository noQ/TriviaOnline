import random
import traceback
import simplejson
import datetime
import mongoengine
from simplejson import JSONDecodeError
from ConfigParser import ParsingError, NoOptionError
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt 
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.exceptions import APIException, MethodNotAllowed, ParseError, \
    NotAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from datastore import DataStore
from util import configparser as cfg
from models import Session, User, Device, Player
from serializers import SessionSerializer 
from controller.session import OnlineChecker
from util.helpers import to_bool
from util.const import POST_METHOD, ten_minutes_in_seconds
from util.auth import AuthToken
from middleware import TokenMiddleware
from social.manager import UserManager 
from parameters import *  
from engine.controller.session import PlayerStatus, GameSession, OnlineChecker, \
    SessionStatus
from engine.serializers import UserSerializer
from bson import json_util
from engine.controller.exceptions import Error, HttpStatus
from engine.controller.rts import PluginHandler, ServerCommand
from engine.controller.client import ServerActionHandler, Action
from TriviaOnline import settings


''' connect to mongodb database '''
try:
    DATABASE_NAME = cfg.Config.getValue("DB", "database")
    DATABASE_PORT = cfg.Config.getValue("DB", "port")
except ( ParsingError, NoOptionError):
    raise Exception("Database configuration error.") 

''' Init DB connection '''
DATABASE  = DataStore(DATABASE_NAME).connect()
''' connect to session collection '''
SESSION_COLLECTION = DATABASE["session"]


class UserRegister(APIView):
    """ 
        Register user using social connectors like facebook
            - url:
            - method: POST
            - data: 
                {"data" : {
                           "token": "c3d1b4d73a38389e",
                           "uuid" : "1116633289",
                           "name" : "Adrian Costia",
                           "id": "1116633289",
                           "email": "adriancostia@aa.com",
                           "country" : "Romania",
                           "city" : "Arad",
                           "about" : "I'm cool",
                           "gender" : "male",
                           "avatar" : "http://facebook.com/avatar..."
                           "device" : "iOS",
                           "push_token" : "edec3d1b4d73a38389e"
                           "registration" : "facebook",
                          } 
                }
                
        Return data:
            {"data": {"token": "c3d1b4d73a38389eec15d8ac8e1479dd23209803", "valability": 60, "uid": 4}, "err": 0}
    """
    def post(self, request):
        """ get data from request """
        try:
            data = JSONParser().parse(request)
            data = data.get(PARAMETER_DATA)
        except JSONDecodeError:
            raise ParseError(detail="No data found on the request")
        
        ''' extract data from post body. first check if all variables are True '''
        if not all( ( data.has_key(PARAMETER_EMAIL), 
                      data.has_key(PARAMETER_FULL_NAME),
                      data.has_key(PARAMETER_ID) 
                      ) ):
            raise ParseError("Some parameters are missing from request")
        
        ''' get all data from request '''
        social_id = WebRequestParameter.get_data(PARAMETER_ID, data)
        email = WebRequestParameter.get_data(PARAMETER_EMAIL, data)
        name  = WebRequestParameter.get_data(PARAMETER_FULL_NAME, data)
        uuid = WebRequestParameter.get_data(PARAMETER_UUID, data)
        avatar = WebRequestParameter.get_data(PARAMETER_AVATAR, data)
        social_token = WebRequestParameter.get_data(PARAMETER_TOKEN, data)
        
        ''' check if user exists '''    
        user = User.objects(email=email, is_active=True).first()
        if user is None:
            ''' create new user using email address'''
            user = User(email=email, username=email)
            if len(name) > 0:
                first_name, last_name = name.split(" ")
                user.first_name = first_name
                user.last_name = last_name
                user.name = name
            user.last_login_time = datetime.datetime.now()
            user.is_active = True
            try:
                user.save()
                user.uid = str(user.id)
            except:
                traceback.print_exc()
                raise APIException("Unable to save user data in DB. Try again later!")
            
        """ add device push token """
        device_type = WebRequestParameter.get_data(PARAMETER_DEVICE, data)
        if device_type:
            push_token = WebRequestParameter.get_data(PARAMETER_PUSH_TOKEN, data)
            if push_token:
                ''' create and add device type '''
                device_obj = Device(type=device_type, push_token=push_token)
                user.devices.append(device_obj) 
        
        """ get or create social connector """
        registration_type = WebRequestParameter.get_data(PARAMETER_REGISTRATION, data)
        if registration_type:
            connector = dict(id=social_id)
            token = WebRequestParameter.get_data(PARAMETER_TOKEN, data)
            if token:
                connector[PARAMETER_TOKEN] = token
                ''' create social connector '''
                social_link = {registration_type : connector}
                UserManager().get_or_create_social_connector(uid=str(user.id), social_link=social_link)    
        
        ''' generate new token '''
        auth_token = AuthToken().generate_auth_token()
        user.auth_token = auth_token        
        ''' save user object '''
        try:
            user.save()
        except:
            raise APIException("Unable to save user data!")
        
        ''' save token in cache '''
        cache_data = dict(uid=user.id, name=name, user=user)
        cache.set(auth_token, cache_data, ten_minutes_in_seconds)
        
        ''' mark user as available '''
        try:
            online = OnlineChecker(user.uid)
            online.is_available()
        except Exception:
            traceback.print_exc()
            pass
        
        ''' return user token '''
        user_token = dict(uid=str(user.id), token=auth_token, valability=ten_minutes_in_seconds)
        """ return response """
        return Response(user_token)


class UserOnlineValidator(APIView):
    """
         Set/Unset if user is online. 
             - accepted values:
                 0 - online
                 1 - onffline
                 n - other status                 
             - mandatory header: auth_token
                 Example: {"AUTH_TOKEN" : "df65ba02a619b685c2e991ae3928da4da31311ed"}
            - call example:
                Http request:
                 - http://localhost:8000/user/online/0/
                 - http://localhost:8000/user/online/1/
                Http response:
                 
    """
    def get(self, request, flag):
        token = TokenMiddleware.get_token(request)
        if token is None:
            raise NotAuthenticated("Token invalid or expired!")
        uid = str(token.get(PARAMETER_UID))
        
        if not isinstance(flag, int):
            try:
                flag = int(flag)
            except TypeError:
                raise ParseError(detail="Flag must be an instance of INT")
        player = OnlineChecker(uid)
        ''' set player status by flag '''
        if flag == PlayerStatus.available.value:
            player.is_available()
        elif flag == PlayerStatus.not_available.value:
            player.not_available()
        else:
            player.set_status(flag)
        
        ''' return total number of players online '''
        count_players = player.count_players()        
        return Response(
                        dict(total=count_players)
                        )


class OnlineUserList(APIView):
    """
         Return a list with all available online players 
             - accepted values:
                 0 - online
                 1 - onffline
                 n - other status                 
             - mandatory header: auth_token
                 Example: {"AUTH_TOKEN" : "df65ba02a619b685c2e991ae3928da4da31311ed"}
            - call example:
                Http request:
                 - http://localhost:8000/user/online/list/
                Http response:
                 - returns total numbers of online players:
                      {"total": 1}
    """    
    def get(self, request, max_players, random_list=True):
        token = TokenMiddleware.get_token(request)
        if token is None:
            raise NotAuthenticated("Token invalid or expired!")
        if not isinstance(max_players, int):
            try:
                max_players = int(max_players)
            except TypeError:
                raise ParseError(detail="MAX_PLAYERS must be an instance of int")
        
        players = []
        try:
            """ get all available players """
            player = OnlineChecker()
            cnt, players = player.get_available_players(max_list=max_players, random_order=random_list)
        except Exception as exc:
            raise APIException(detail=exc)
        
        ''' get players details '''
        response_data = []
        if len(players) > 0:
            ''' extract players based on uid '''
            players = User.objects(uid__in=players)
            if len(players) > 0: 
                ''' serialize players '''
                serializer = UserSerializer(players, many=True)
                response_data = serializer.data
        return Response(response_data)
        

class SessionView(APIView):
    """
        Create or get game session with number of players
        - players are slots in the game. Default slots = 2
        
        - call example:
                Http request:
                 - http://localhost:8000/game/session/
                         {"data" : {
                                      "slots" : 2
                                   }
                         }                 
                Http response:
                 - returns game session information:
                    {
                        "status": 1,
                        "players": [{
                                "info": {
                                    "ranking": 0,
                                    "name": "Vasile Ion",
                                    "city": null,
                                    "country": null,
                                    "title": "Beginner",
                                    "avatar": null
                                },
                                "status": 3,
                                "uid": "5322f1138d8c7d2bd01b3db9"
                            }, {
                                "info": {
                                    "ranking": 0,
                                    "name": "Adrian Costia",
                                    "city": null,
                                    "country": null,
                                    "title": "Beginner",
                                    "avatar": null
                                },
                                "status": 2,
                                "uid": "534bdfda8d8c7d028452593a"
                            }],
                        "slots": 0,
                        "rtserver": {},
                        "name": "fe14b5"
                    }
    """
    
    """ game available slots: 1 vs. 1 """
    DEFAULT_SLOTS = 2
    ''' return a list with MAX available players '''
    MAX_PLAYERS_TO_SEARCH = 10
    ''' auto join '''
    AUTO_JOIN = True
    GAME_NAME = "trivia"
    
    def post(self, request):
        token = TokenMiddleware.get_token(request)
        if token is None:
            raise NotAuthenticated("Token invalid or expired!")
        ''' check if token has user attribute '''
        if not token.has_key("user"):
            raise NotAuthenticated()
        user = token.get("user")
        uid  = user.uid
        
        """ get data from request """
        try:
            data = JSONParser().parse(request)
            data = data.get(PARAMETER_DATA)
        except JSONDecodeError:
            raise ParseError(detail="No data found on the request")
        
        ''' get game name '''
        game_name = WebRequestParameter.get_data(PARAMETER_GAME_NAME, data)
        if game_name is None:
            game_name = self.GAME_NAME
        
        ''' get numbers of players to play this game '''
        game_slots = WebRequestParameter.get_data(PARAMETER_SLOTS, data)
        if game_slots is None:
            game_slots = self.DEFAULT_SLOTS
        else:
            if not isinstance(game_slots, int):
                try:
                    game_slots = int(game_slots)
                except TypeError:
                    raise ParseError(detail="SLOTS must be an instance of int")
            
        ''' pickup players in random order '''
        random_order = WebRequestParameter.get_data(PARAMETER_RANDOM, data)
        if random_order is None:
            random_order = False
        else:
            random_order = to_bool(random_order)

        ''' return a list with max players available (online) '''
        search_max_players = WebRequestParameter.get_data(PARAMETER_MAX_PLAYERS_TO_SEARCH, data)
        if search_max_players is None:
            search_max_players = self.MAX_PLAYERS_TO_SEARCH
        
        ''' auto join in game '''
        auto_pickup = WebRequestParameter.get_data(PARAMETER_AUTO_PICKUP, data)
        if auto_pickup is None:
            auto_pickup = self.AUTO_JOIN

        player = OnlineChecker()
        ''' create/get game session '''        
        sess = GameSession(user=user)
        ''' 1. check if current user not belongs to other session '''
        session = sess.get_awaiting_sessions()
        if session is None:
            ''' set game name '''
            sess.set_game_name(game_name)
            ''' create new session with one player (the session owner) '''
            sess.create()
            ''' pick up random players if available from a list with MAX_PLAYERS '''
            player = OnlineChecker()
            cnt, players = player.get_available_players(
                                                        max_list=search_max_players,
                                                        random_order=random_order
                                                        )
            if cnt == 0:
                ''' if no one is online then play this game using bot player '''
                return Error("No online players available!",
                              HttpStatus.NO_ONLINE_PLAYERS.value
                            ).show()
            ''' shuffle players '''
            '''
            if uid in players:
                try:
                    players.remove(str(uid))
                except ValueError:
                    pass
            ''' 
            random.shuffle(players)
            ''' just pick the players needed to start the game '''
            if cnt < sess.get_available_slots():
                return Error("Not enough players to start the game!",
                                 HttpStatus.NOT_ENOUGHT_PLAYERS.value
                                 ).show()                    
            
            if cnt > game_slots:
                players = players[:game_slots]
            ''' extract players by UID '''
            print "players: " + str(players)
            users =  User.objects(uid__in=players)
            if len(users) == 0:
                raise APIException("No users found in DB!")
            ''' add players in session '''
            has_players = False
            for user in users:
                ''' if has enough slots then join '''
                if not sess.has_free_slots():
                    break
                ''' add players in session '''
                player = Player(uid = user.uid,
                            status = PlayerStatus.not_ready.value
                        )
                ''' set player additional info '''
                player.get_player_info(user)
                ''' add player to current session '''
                sess.add_player(player)
                ''' set available game slots '''                
                sess.get_session().available_slots -= 1
                has_players = True
            if has_players:
                sess.get_session().save()
                
            ''' get session players '''
            players = sess.get_players()
            if players is None:
                return Error("No players found in current session!").show()
            
            try:
                ''' create RTS session '''
                action = Action.create_session(sess, self.DEFAULT_SLOTS, player)
                client = ServerActionHandler(
                                             (settings.GAME_SERVER_ADDRES, 
                                              settings.GAME_SERVER_PORT)
                                             )
                client.set_data(action)
                client.send()
            except:
                traceback.print_exc()
            return Response(players)
        
        else:
            ''' check if session is expired '''
            session_time = sess.get_session().expired_at
            if sess.is_expired(session_time):
                ''' get session owner and set flag: is_available to play other game '''
                session_owner = sess.get_session().owner_uid
                session_name = sess.get_session().name
                player.set_uid(session_owner)
                player.is_available()
                ''' destroy session is expired '''
                sess.destroy(session_name)
                
                return Error("Session is expired!", HttpStatus.SESSION_EXPIRED).show()
            ''' if session has free slots then join in session '''
            if sess.has_free_slots():
                if sess.can_join():
                    return Response(sess.get_players())
                else:
                    ''' return error message if session is full '''
                    return Error("Unable to join. Session is full!",
                                     HttpStatus.SESSION_FULL.value
                                     ).show()
            else:
                ''' set player status to ready to play '''
                players = sess.set_player_status(sess.user.uid,
                                                 PlayerStatus.ready_to_play.value
                                                 )
                if players is None:
                    return Error("No players found in current session!").show()
                ''' set session status ready to play '''
                sess.get_session().status = SessionStatus.ready_to_play.value
                sess.get_session().save()
                
                ''' join user to sesssion '''
                try:
                    action = Action.join_session(sess, sess.user)
                    client = ServerActionHandler(
                                                 (settings.GAME_SERVER_ADDRES, 
                                                  settings.GAME_SERVER_PORT
                                                  )
                                                 )
                    client.set_data(action)
                    client.send()
                except:
                    traceback.print_exc()
                
                return Response(sess.get_players())
        raise APIException("Unable to process data!")

        
class PlayGameView(APIView):
    """
        Prepare to play game
        
        - call example:
                Http request:
                 - http://localhost:8000/game/play/
                    {
                       "data" : {
                                 "session" : "fe14b5"
                                }
                    }
                                     
                Http response:
                    {
                        "port": 11000,
                        "server": "10.100.63.48"
                    }                 
            
    
    """
    def post(self, request):
        token = TokenMiddleware.get_token(request)
        if token is None:
            raise NotAuthenticated("Token invalid or expired!")
        ''' check if token has user attribute '''
        if not token.has_key("user"):
            raise NotAuthenticated()
        user = token.get("user")
        uid  = user.uid
        
        """ get data from request """
        try:
            data = JSONParser().parse(request)
            data = data.get(PARAMETER_DATA)
        except JSONDecodeError:
            raise ParseError(detail="No data found on the request")
        
        session_name = WebRequestParameter.get_data(PARAMETER_SESSION, data)
        if session_name is None:
            raise ParseError(detail="Game session is not set on the request")
        
        ''' get session '''
        game_session = GameSession()
        ''' check if session exists '''
        if not game_session.find_session(session_name):
            return Error("Unable to join. Invalid session",
                         HttpStatus.SESSION_INVALID.value
                         ).show()
        ''' get plugin data '''
        session = game_session.get_session()
        if session is None:
            raise APIException("No session found with ID %s" % session_name)
        ''' load plugin data '''
        if session.game_name is None:
            raise APIException("Game is not set on session with ID %s" % session_name)
        
        ''' load plugin dictionary '''
        from TriviaOnline.settings import PLUGINS
        ''' get plugin by name '''
        plugin = PluginHandler.get_from_dict(PLUGINS, str(session.game_name))
        ''' check if session has game logic set '''
        game_logic = game_session.has_game_logic()
        if game_logic is None:
            ''' get game logic from plugin '''
            game_logic = plugin.game_logic()
            if game_logic:
                game_session.set_game_logic(game_logic)

        ''' get server info '''
        server_info = plugin.get_server_info()
        ''' check session on RT server '''
        try:
            action = Action.check_session(session_name)
            client = ServerActionHandler(
                                         (settings.GAME_SERVER_ADDRES, 
                                          settings.GAME_SERVER_PORT
                                          )
                                         )
            client.set_data(action)
            client.send()
            ''' retrieve data from server '''
            data = str(client.get_reveived_data())
            if data == ServerCommand.NO_DATA or data == ServerCommand.FAILED:
                raise APIException("Session not found on RT server!")
        except:
            traceback.print_exc()
            raise APIException("Unable to retrieve data from RT server!")
        
        response = {
                    'server' : server_info,
                    'game_logic' : game_logic
                    }
        ''' construct response '''
        return Response(response)
        

