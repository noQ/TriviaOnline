import json
from enum import IntEnum
from django.http.response import HttpResponse

class HttpStatus(IntEnum):
    SUCCESS                 = 0
    REST_EXCEPTION          = -1
    JSON_PROTOCOL_ERROR     = -2
    METHOD_NOT_DEFINED      = -3
    HTTPS_NOT_USED          = -4
    JSON_INVALID            = -5
    DB_ERROR                = -6
    WEB_PARAMETER_NOT_FOUND = -7
    TOKEN_INVALID           = -8
    INVALID_DATA            = -9
    SESSION_INVALID         = 10
    SESSION_FULL            = 11
    SESSION_EXPIRED         = 12
    NOT_ENOUGH_PLAYERS      = 20
    NO_ONLINE_PLAYERS       = 30
    CONTINUE                = 100
    SWITCHING_PROTOCOLS     = 101
    OK                      = 200
    CREATED                 = 201 
    ACCEPTED                = 202
    NON_AUTHORITATIVE_INFORMATION = 203
    NO_CONTENT              = 204
    RESET_CONTENT           = 205
    PARTIAL_CONTENT         = 206
    MULTIPLE_CHOICES        = 300
    MOVED_PERMANENTLY       = 301
    FOUND                   = 302
    SEE_OTHER               = 303
    NOT_MODIFIED            = 304
    USE_PROXY               = 305
    RESERVED                = 306
    TEMPORARY_REDIRECT      = 307
    BAD_REQUEST             = 400
    UNAUTHORIZED            = 401
    PAYMENT_REQUIRED        = 402
    FORBIDDEN               = 403
    NOT_FOUND               = 404
    METHOD_NOT_ALLOWED      = 405
    NOT_ACCEPTABLE          = 406
    PROXY_AUTHENTICATION_REQUIRED = 407
    REQUEST_TIMEOUT         = 408
    CONFLICT                = 409
    GONE                    = 410
    LENGTH_REQUIRED         = 411
    PRECONDITION_FAILED     = 412
    REQUEST_ENTITY_TOO_LARGE = 413
    REQUEST_URI_TOO_LONG    = 414
    UNSUPPORTED_MEDIA_TYPE  = 415
    REQUESTED_RANGE_NOT_SATISFIABLE = 416
    EXPECTATION_FAILED      = 417
    INTERNAL_SERVER_ERROR   = 500
    NOT_IMPLEMENTED         = 501
    BAD_GATEWAY             = 502
    SERVICE_UNAVAILABLE     = 503
    GATEWAY_TIMEOUT         = 504
    HTTP_VERSION_NOT_SUPPORTED  = 505
    INACTIVE_USER           = 506

class Error(object):
    content_type = "application/json; charset=UTF-8"
    
    def __init__(self, message, status=HttpStatus.NOT_FOUND.value):
        self.message = message
        self.status  = status
        
    def show(self, message=None):
        data = {
                 "desc": self.message,
                 "data": None,
                 "err": self.status
                }
        data = json.dumps(data)
        return HttpResponse(data, status=HttpStatus.OK.value, mimetype=self.content_type)

    
