from rest_framework.exceptions import ParseError
from util.helpers import to_bool

class WebRequestParameter(object):
    """
        Manipulate web requests parameters
            Example:
                WebRequestParameter.check_parameters([postid, eventid], **kwargs)
                WebRequestParameter.check_and_get(postid, **kwargs)
    """   
    @staticmethod
    def get_data(key, from_data):
        return from_data.get(key) if from_data.has_key(key) else None
     
    @staticmethod
    def check_key(key, **kwargs):
        if not kwargs.has_key(key):
            _msg = "Parameter '%s' not found in the web request!" % (key)
            raise ParseError(_msg)
    
    ''' check/get web parameter '''
    @staticmethod
    def get(parameter, **kwargs):
        if parameter is None:
            message = "%s is invalid!" % (parameter)
            raise ParseError(message)
        parameter_value = None
        if kwargs.has_key(parameter):
            parameter_value = kwargs.get(parameter)
        return parameter_value
    
    @staticmethod
    def check_and_get(parameter, error_message='Invalid request parameter', **kwargs):
        parameter_value = WebRequestParameter.get(parameter, **kwargs)
        if parameter_value is None:
            raise ParseError(error_message)
        if isinstance(parameter_value, (basestring, str, list, dict)):
            if len(parameter_value) == 0:
                _msg = "%s length zero!" % (parameter_value)
                raise ParseError(_msg)
        return parameter_value    

    @staticmethod
    def check_parameters(parameter):
        if isinstance(parameter, list):
            for param in parameter:
                WebRequestParameter.check_parameter(param)
        else:
            WebRequestParameter.check_parameter(param)

    @staticmethod
    def check_parameter(parameter):
        ''' check parameter and return data '''
        if parameter is None:
            _msg_invalid = "%s is invalid!" % (parameter)            
            raise ParseError(_msg_invalid)
        if isinstance(parameter, (basestring, str, list, dict, unicode)):
            if len(parameter) == 0:
                _msg = "%s length zero!" % (parameter)
                raise ParseError(_msg)
        elif isinstance(parameter, bool):
            to_bool(parameter)
        return parameter
    
    @staticmethod
    def get_uid(**kwargs):
        return WebRequestParameter().get(PARAMETER_UID, **kwargs)
    
    @staticmethod
    def check_uid(**kwargs):
        uid = WebRequestParameter().get(PARAMETER_UID, **kwargs)
        if uid is None:
            raise ParseError("UID not set")
        return uid


PARAMETER_DATA     = "data"
PARAMETER_ID       = "id"
PARAMETER_UID      = "uid"
PARAMETER_UUID     = "uuid"
PARAMETER_DEVICE   = "device"
PARAMETER_PUSH_TOKEN = "push_token"
PARAMETER_REGISTRATION = "registration"
PARAMETER_USER     = "user"
PARAMETER_USERNAME = "username"
PARAMETER_PASSWORD = "password"
PARAMETER_TOKEN = "token"
PARAMETER_EMAIL    = "email"
PARAMETER_FULL_NAME = "name"
PARAMETER_FIRST_NAME = "first_name"
PARAMETER_LAST_NAME = "last_name"
PARAMETER_AVATAR = "avatar"
PARAMETER_PLAYERS = "players"
PARAMETER_SLOTS = "slots"
PARAMETER_RANDOM = "random"
PARAMETER_SESSION   = "session"
PARAMETER_MAX_PLAYERS_TO_SEARCH = "search_list"
PARAMETER_AUTO_JOIN = "auto_join"
PARAMETER_AUTO_PICKUP = "auto_pickup"
PARAMETER_CATEGORY_ID = "catid"
PARAMETER_CATEGORY = "category"
PARAMETER_QUESTION  = "question"
PARAMETER_OPTIONS   = "options"
PARAMETER_ANSWER    = "answer"
PARAMETER_TIME      = "time"
PARAMETER_TYPE      = "type"
PARAMETER_SCORE     = "score"
PARAMETER_GAME_NAME = "game_name"



