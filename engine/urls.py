from django.conf.urls import patterns, include, url
from engine.views import UserRegister, UserOnlineValidator, OnlineUserList, \
    SessionView, PlayGameView

urlpatterns = patterns('',
    url(r'^user/register/$', 'engine.views.user_create'),
    # register new user using social connector FB
    url(r'^user/register/social/$', UserRegister.as_view()),
    # authenticate user using facebook social ID
    url(r'^user/authenticate/social/$', 'engine.views.authenticate_social'),    
    # authenticate user using classic system: username/password
    url(r'^user/authenticate/$', 'main.views.login'),
                       
    # set or unset if user is online: 1 - is online, 0 - is offline
    url(r'^user/online/(?P<flag>[0-9]+)/$', UserOnlineValidator.as_view()),
    # returns a list with available players 
    url(r'^user/online/list/$', OnlineUserList.as_view()),
    url(r'^user/online/list/(?P<max_players>[0-9]+)/$', OnlineUserList.as_view()),
    
    # create new game session 
    url(r'^game/session/$', SessionView.as_view()),
    url(r'^game/session/(?P<max_players>[0-9]+)/$', SessionView.as_view()),
    # play game
    url(r'^game/play/$', PlayGameView.as_view()),
    
)

