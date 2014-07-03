from django.conf.urls import patterns, include, url
from game.views import LeaderboardTable, Categories, TurnQuestions, \
    RandomQuestions, CategoryQuestions, ResolveQuestion, AddQuestion, \
    UserScore, Home

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'main.views.index'),
    
    # get trivia categories
    url(r'^trivia/categories/$', Categories.as_view()),
    # generate new turn questions, where 'turn' = no of turns, 'questions'=total questions per round
    url(r'^trivia/questions/turn/(?P<turn>\d)/(?P<questions>\d)/$', TurnQuestions.as_view()),
    # generate turn questions -> 5 rouns with 10 questions each
    url(r'^trivia/questions/turn/$', TurnQuestions.as_view()),
    # get random questions with 'limit' or not. Default limit is 10     
    url(r'^trivia/questions/$', RandomQuestions.as_view()),
    url(r'^trivia/questions/(?P<limit>\w+)$', RandomQuestions.as_view()),
    # get trivia categories
    url(r'^trivia/questions/category/(?P<category>\d{1})/$', CategoryQuestions.as_view()),
    url(r'^trivia/questions/category/(?P<category>\d{1})/(?P<limit>\d)/$', CategoryQuestions.as_view()),
    # resolve trivia questions
    url(r'^trivia/questions/resolve/$', ResolveQuestion.as_view()),
    # submit score
    url(r'^trivia/score/$', UserScore.as_view()),
    # add new trivia question
    url(r'^trivia/questions/add/$', AddQuestion.as_view()),
    # display trivia leaderboards
    url(r'^trivia/leaderboard/$', LeaderboardTable.as_view()),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),
)
