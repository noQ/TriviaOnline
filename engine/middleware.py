import re
import json
from django.core.cache import cache
from rest_framework.response import Response
from django.http.response import HttpResponse
from django.core.exceptions import MiddlewareNotUsed

def findpath(path):
    return re.compile(r'\b({0})\b'.format(path), flags=re.IGNORECASE).search

def raise_error(message):
    content_type = "application/json; charset=UTF-8"    
    data = {
             "err_class": "main.exceptions.AuthenticationError",
             "err_desc": message,
             "data": None,
             "err": 401
            }
    plain = json.dumps(data)
    return HttpResponse(plain, status=200, mimetype=content_type)

class TokenMiddleware(object):
    """ 
        Authenticate using token from AUTH_TOKEN
    """
    AUTH_TOKEN = "HTTP_AUTH_TOKEN"
    ADMIN_URL = "admin"
    EXCLUDE_FROM_RULE = ["/user/register/", "/user/register/social/", "/user/create/", "/user/token/",
               "/user/authenticate/social/", "/user/authenticate/"]

    def __init__(self):
        self.raise_error = False
        self.error_message = None
    
    @staticmethod
    def get_token(request):
        if hasattr(request._request, TokenMiddleware.AUTH_TOKEN.lower()):
            if request._request.http_auth_token:
                return request._request.http_auth_token
        return None
    
    def process_response(self, request, response):
        if self.raise_error:
            message = self.message
            self.raise_error = False
            self.message = None
            return raise_error(message)
        return response
        
    def process_request(self, request):
        if not findpath(self.ADMIN_URL)(request.path):
            if str(request.path) not in self.EXCLUDE_FROM_RULE:
                if not request.META.has_key(self.AUTH_TOKEN):
                    self.raise_error = True
                    self.message = "Token not found in the request"                    
                else:
                    auth_token = request.META.get(self.AUTH_TOKEN)
                    if auth_token is None:
                        self.raise_error = True
                        self.message = "Invalid token"                    
                    elif len(auth_token) == 0:
                        self.raise_error = True
                        self.message = "Token length zero!"                    
                    else:
                        token = cache.get(auth_token)
                        if token is None:
                            self.raise_error = True
                            self.message = "Token Invalid! Try to authenticate."                                                
                        self.has_error = False
                        request.http_auth_token = token
