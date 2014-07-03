import random
import traceback
import mongoengine
from django.utils import simplejson
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt  # just add
from rest_framework.views import APIView
from rest_framework.exceptions import *
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from game.models import Category, Question, AnswerSettings, ScoreDetails
from game.response import Leader, QuestionResponse, CategoryResponse
from engine.cacheobjects import ObjectMemoryCache
from engine.middleware import TokenMiddleware
from engine.parameters import *
from engine.models import Leaderboard, GameType, User, LeaderboardType, UserRank
from engine.serializers import LeaderboardSerializer
from simplejson import JSONDecodeError


def slice(count, limit):
    rand = int(random.random() *  count )
    if not isinstance(limit, int):
        limit = int(limit)
    next = rand + limit
    return rand, next

def security_token(token):
    if token is None or len(token) == 0:
        return False
    token = cache.get(token)
    if token is None:
        return False
    return True

def get_all_questions():
    """
        Retrieve all question from DB and save to HashMap
        note: this will take a while to load but the web call response will be between 1-5 millisec.
    """
    questions = ObjectMemoryCache.get_key(Question)
    if questions is None:
        questions = Question.objects
        ''' set in cache '''
        memo = ObjectMemoryCache(Question, "qid")
        memo.queryset(questions)
        memo.load(serialize=True, serializer_class=QuestionResponse)
        ''' get key '''
        questions = ObjectMemoryCache.get_key(Question)
    return questions
    

def level_up(user, leaderboard):
    """
        User level up
    """
    next_ranking = user.ranking + 1
    rank = UserRank().get(next_ranking)
    if rank is None:
        return None
    
    level_up, score_detail = False, {}
    if leaderboard.score > rank.points:
        ''' get next ranking '''
        next_ranking += 1 
        rank = UserRank().get(next_ranking)
        level_up = True
    level = dict(next_rank=rank.ranking, 
                 max_points=rank.points)
    ''' for levelup update user object '''
    if level_up:
        score_detail["levelup"] = level_up
        user.ranking = next_ranking
        user.save()
    
    level["ranking"] = user.ranking
    score_detail["level"] = level
    score_detail["total_score"] = leaderboard.score
    return user, score_detail
    

class Home(APIView):
    def get(self, request):
        content = dict(message = "Trivia Works!")
        return Response(content)

    
class LeaderboardTable(APIView):
    """
        Get leaderboards views
        - by default retrieve first 20 users
        - result will be retrieved from cache (10 minutes)
    """
    def get(self, request, limit=20):
        token = TokenMiddleware.get_token(request)
        if token is None:
            raise NotAuthenticated("Token invalid or expired!")
        uid = str(token.get(PARAMETER_UID))
        
        leader_table = ObjectMemoryCache.get_key(Leaderboard)
        if leader_table:
            leader_table = leader_table.values()
        else:
            ''' retrieve X leaders from leaderboard table '''
            leader_table = Leaderboard.objects[:limit]
            if len(leader_table) == 0:
                return []
            memo = ObjectMemoryCache(Leaderboard, PARAMETER_ID)
            memo.queryset(leader_table)
            memo.load(serialize=True, serializer_class=Leader)
            leader_table = memo.get_key(Leaderboard)
        return Response(leader_table)
            
        
class Categories(APIView):
    '''
        Get all categories
            -url: http://localhost:8000/trivia/categories/
    '''
    def get(self, request):
        categories = ObjectMemoryCache.get_key(Category)
        if categories:
            categories = categories.values()
        else:
            ''' extract all categories with status 'active' true '''
            categories = Category.objects(active=True)
            if len(categories) == 0:
                return Response([])
            ''' put categories in memory '''
            memo = ObjectMemoryCache(Category, PARAMETER_CATEGORY_ID)
            memo.queryset(categories)
            loaded, categories = memo.load(serialize=True, serializer_class=CategoryResponse)
            if not loaded:
                raise APIException(detail="Unable to load categories")            
        return Response(categories)
        

class CategoryQuestions(APIView):
    """
        Get questions by category ID
        
    """
    def get(self, request, category, limit=10):
        cache_key = "q%s" % str(category)
        questions = cache.get(cache_key)
        if questions is None:
            questions = Question.objects(category=category, approved=True)
            if questions.count() == 0:
                return Response({})
            questions = [QuestionResponse(q).serialize() for q in questions]
            cache.set(cache_key, questions)
            
        random_questions = random.sample(questions, int(limit))
        if len(random_questions) == 0:
            random_questions = {}    
        return Response(random_questions)
    

class TurnQuestions(APIView):
    """
        Get turn questions. default 5 turns and 10 questions per turn.
        
        URL:
            - http://localhost:8000/trivia/questions/turn/
            - http://localhost:8000/trivia/questions/turn/2/3/
                where: 2 - numbers of turns per round
                       3 - number of questions per turn
        METHOD: GET
    """
    def get(self, request, turn=5, questions=10):
        if not isinstance(turn, int):
            turn = int(turn)
        if not isinstance(questions, int):
            questions = int(questions)
        
        limit = turn * questions
        """ get questions """
        quest = get_all_questions()
        if len(quest) == 0:
            return { }
        
        quest_list = random.sample(quest.values(), limit)
        if len(quest_list) == 0:
            return {}
        ''' split list by numbers of turns 
            note: [iter(s)]*n makes a list of n times the same iterator for s.
        '''
        zipped = zip(*[iter(quest_list)] * questions)
        ''' recreate the list '''
        questions = { }
        key = 1
        for step in xrange(turn):
            questions[str(key)] = list(zipped[step])
            key += 1
        return Response(questions)


class RandomQuestions(APIView):
    """
        Get random questions
            -url: http://localhost:8000/trivia/questions/
                  http://localhost:8000/trivia/questions/2
    """
    def get(self, request, limit=10):
        questions = get_all_questions()
        random_questions = random.sample(questions.values(), int(limit))
        if len(random_questions) == 0:
            random_questions = {}    
        return Response(random_questions)
    

class ResolveQuestion(APIView):
    """
        Resolve question(s) by ID(s)
            - url:
            - method: POST
            - data (example):
                    {"data" : {"9" : 3, "41": 3} }
                    where 1: is question id
                          2: is the user answer for that question
            - return:
                    {"9": [true, 3], "41": [false, -1]}
                        where:
                            5 - is the question id
                            [false, 0] - first value:  answer is correct
                                       - second value: correct answer (-1, invalid)
    """
    def post(self, request):
        try:
            data = JSONParser().parse(request)
            data = data.get(PARAMETER_DATA)
        except JSONDecodeError:
            raise ParseError(detail="No data found on the request")
        
        resolved_questions = {}
        ids = [int(key) for key in data.keys()]    
        if len(ids) > 0:
            questions = Question.objects(qid__in=ids)
            if len(questions) > 0:
                ''' compare result '''
                resolved_questions = self.resolve_question(data, questions)
        return Response(resolved_questions)
    
    def resolve_question(self, data, questions):
        resolve = {}
        for q in questions:
            ''' get question id '''
            id = str(q.qid)
            answer = [False, -1]
            if data.has_key(id):
                if data[id] == q.real_answer:
                    answer[0] = True
                    answer[1] = q.real_answer
                resolve[id] = answer
        return resolve

class AddQuestion(APIView):
    """
        Add new question
        
         - url: http://localhost:8000/trivia/questions/add/
         - method: POST
         - data:
             { "data" : {"question": "Blue is red?", "options": ["a", "b", "c", "d"],
              "category" : 1, "answer" : 3 }
             }
         - response: True
        
    """
    def post(self, request):
        try:
            data = JSONParser().parse(request)
            data = data.get(PARAMETER_DATA)
        except JSONDecodeError:
            raise ParseError(detail="No data found on the request")
        
        ''' check all values '''
        catid    = WebRequestParameter.get_data(PARAMETER_CATEGORY, data)
        question = WebRequestParameter.get_data(PARAMETER_QUESTION, data)
        options  = WebRequestParameter.get_data(PARAMETER_OPTIONS, data)
        answer   = WebRequestParameter.get_data(PARAMETER_ANSWER, data)
        
        if not all( (catid, question, options, answer ) ):
            raise ParseError(detail="Some parameters are missing from request")
        
        ''' search for category '''
        category = Category.objects(catid = int(catid)).first()
        if category is None:
            raise APIException("Category not exists!")
        
        try:
            self.add_question(category, question, options, answer)
        except:
            traceback.print_exc()
            raise APIException("Unable to add question. Try again later!")
        return Response(True)
        
    
    def add_question(self, category, question, options, answer):
        ''' extract data from json '''
        catid = category.catid
        question = Question(category=catid,
                            question=question,
                            real_answer=answer
                            )
        ''' extract options for question '''
        quiz_options = ['a', 'b', 'c', 'd']
        for k, v in enumerate(options):
            var = "var_%s" % quiz_options[k]
            setattr(question, var,  options[k])
        question.save()
    

class UserScore(APIView):
    """
        Submit game score
            -url : trivia/score/
            - method: POST
            - data: 
                {"data" : {"score" :  [{"id": "5", "answer": 3, "time": 2 }, {"id": "6", "answer": 1, "time": 6 }], "type" : 1  } }
                - where:
                    - "id" - question ID
                    - "answer" : user answer option. Answer will be checked on server if is correct or not.
                    - "time" : user answered in X seconds
                    - "type" : game type. This field is optional and default value is None
            - returns data:
                {"total_score": 11, "game_score": 1.0, "levelup": true, "level": {"ranking": 2, "max_points": 15, "next_rank": 2}}
    """
    DEFAULT_GAME_TYPE = 1
    ''' general '''
    DEFAULT_LEADER_TYPE = 1
    
    def post(self, request):
        ''' check user token '''
        token = TokenMiddleware.get_token(request)
        if token is None:
            raise NotAuthenticated("Token invalid or expired!")

        try:
            data = JSONParser().parse(request)
            data = data.get(PARAMETER_DATA)
        except JSONDecodeError:
            raise ParseError(detail="No data found on the request")
        game_type = WebRequestParameter.get_data(PARAMETER_TYPE, data)

        ''' extract user from token '''
        if not token.has_key(PARAMETER_USER):
            raise NotAuthenticated()
        ''' get user object from request '''
        user = token.get(PARAMETER_USER)
        if user is None:
            raise NotAuthenticated("User not exists!")

        score = WebRequestParameter.get_data(PARAMETER_SCORE, data)
        if not isinstance(score, list):
            raise APIException("Object must be an instance of list")
        
        ''' update user score '''
        user, score_detail = self.update_score(user, score, game_type)
        if score_detail.has_key("levelup"):
            token = TokenMiddleware.get_token(request)
            if token:
                from engine.util.const import ten_minutes_in_seconds
                cache_data = dict(uid=user.id, name=user.name, user=user)
                cache.set(user.auth_token, cache_data, ten_minutes_in_seconds)
        return Response(score_detail)
    
        
    def update_score(self, user, score, game_type):
        ''' get game type if exists '''
        if game_type is None:
            game_type = self.DEFAULT_GAME_TYPE
            
        game_obj = GameType.objects(typeid = game_type).first()
        if game_obj is None:
            ''' get default game type '''
            game_obj = GameType.objects(typeid = self.DEFAULT_GAME_TYPE)
        ''' get default leaderboard type '''
        leaderboard_type = LeaderboardType.objects(typeid = self.DEFAULT_LEADER_TYPE).first()
            
        ''' extract items from array '''
        try:
            questions_ids = [int(d.get(PARAMETER_ID)) for d in score]
        except KeyError:
            raise ParseError("ID argument not found in the data field")
                
        user_score = {}
        total_score = 0
        leaderboard = None
        if len(questions_ids) > 0:
            ''' get questions from DB '''
            questions = Question.objects(qid__in=questions_ids)        
            if len(questions) > 0:
                score_objects = []
                leaderboard = Leaderboard.objects(uid=user.uid).first()
                if leaderboard is None:
                    ''' create new entry in leaderboard if not exists '''
                    leaderboard = Leaderboard(uid=user.uid,
                                              full_name = user.name,
                                              corect_answers = 0,
                                              skipped = 0,
                                              kind = leaderboard_type,
                                              total_answers = 0
                                              )
                    
                ''' extract settings from cache '''
                answer_settings = ObjectMemoryCache.get_key(AnswerSettings)
                
                ''' for each item create score '''
                real_score = 0 
                for item in score:
                    id = item.get("id")
                    user_answer = item.get("answer")
                    time = item.get("time")
                    
                    ''' extract time coef. this will be used to calculate user score '''
                    time_coef = 0
                    if answer_settings and answer_settings.has_key(time):
                        settings = answer_settings.get(time)
                        if hasattr(settings, "coeficient"):
                            time_coef = settings.coeficient
                    ''' calculate score based on submited question '''   
                    for q in questions:
                        ''' check if questions is present in the user request data '''
                        if int(q.qid) == int(id):
                            valid_answer = False
                            ''' check if user give us the right answer for selected question '''
                            if q.real_answer == user_answer:
                                valid_answer = True
                                leaderboard.corect_answers += 1
                            else:
                                leaderboard.skipped += 1
                                
                            ''' create score object '''
                            score = ScoreDetails(uid=user.uid,
                                                 question=q, 
                                                 correct_answer=valid_answer,
                                                 answer_time=time,
                                                 game_type = game_obj
                                                 )
                            ''' calculate score based on answer time coef '''
                            if valid_answer:                        
                                score.calculate_score(time_coef)
                                ''' get user score '''
                                real_score += score.get_user_score()
                            else:
                                score.score = 0
                            leaderboard.total_answers += 1
                                                        
                            score_objects.append(score)
                            break
                if len(score_objects) > 0:
                    try:
                        ''' save score in DB '''
                        for score in score_objects:
                            total_score += score.score
                            score.save()
                        ''' save leader board '''
                        leaderboard.score += int(round(real_score))
                        leaderboard.save()
                    except:
                        traceback.print_exc()

        ''' check user level '''
        score_detail = {}
        if leaderboard:
            user, score_detail = level_up(user, leaderboard)
        score_detail["game_score"] = total_score
        return user, score_detail
