from engine.models import Mission, Category, Score
from mongoengine import Document
from mongoengine.fields import *
 

class Question(Document, Mission):
    ''' Define trivia questions '''
    qid         = SequenceField(required=True)
    question    = StringField(required=True)
    var_a       = StringField(verbose_name='Variant A')
    var_b       = StringField(verbose_name='Variant B')
    var_c       = StringField(verbose_name='Variant C')
    var_d       = StringField(verbose_name='Variant D')
    real_answer = IntField(verbose_name='Answer')
    category    = IntField(required=True)
    #status      = BooleanField(default=True, verbose_name='Status')
    approved    = BooleanField(default=True, verbose_name='Question is Approved ?')

    meta = {
        'collection': 'questions',
        'indexes':  ['qid'], 
        'ordering': ['qid']
        }
    
    def __unicode__(self):
        return str(self.qid)
    
    def get_all_questions(self):
        return Question.objects
    
    def get_question_by_id(self, id):
        if not isinstance(id, list):
            id = list(id)
        return Question.objects(qid__in = id)
    
    def get_by_category_name(self, category):
        if category:
            return Question.objects(category__name=category)
        return None
    
class AnswerSettings(Document):
    id         = IntField(required=True)
    seconds    = IntField(verbose_name='Answer in seconds')
    coeficient = FloatField(required=False)

    meta = {
        'collection':'answer_settings',
        'indexes':  ['id'], 
        'ordering':['id']
        }
    
    def __unicode__(self):
        return str(self.id)

class ScoreDetails(Document, Score):
    CORECT_ANSWER_POINT = 1
        
    question        = ReferenceField('Question')
    correct_answer  = BooleanField(default=False)
    answer_time     = IntField(verbose_name="Answered time (seconds)")
    total_answers   = IntField(verbose_name="Total answers")

    meta = {
        'collection':'score',
        'indexes':  ['id'], 
        'ordering':['id']
        }
    
    def __unicode__(self):
        return "%s - %s" % ( str(self.uid), str(self.score))

    def calculate_score(self, time_coef):
        self.score = self.CORECT_ANSWER_POINT + float(time_coef)
    
    def get_user_score(self):
        return self.score
