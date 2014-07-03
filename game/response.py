"""
    Define response classes
"""

class BaseResponse(object):
    def __init__(self, model):
        self.model = model
    
    def serialize(self, request=None):
        raise NotImplemented

class Leader(BaseResponse):
    def serialize(self, request=None):
        return {
                "id" : self.model.id,
                "username" : self.model.user.username,
                "full_name" : self.model.user.get_full_name(),
                "total" : self.model.total_answers,
                "corect" : self.model.corect_answers,
                "skipped" : self.model.skipped,
                "added" : self.model.questions_added,
                "score" : self.model.score
                }

class CategoryResponse(BaseResponse):
    def serialize(self, request=None):
        return {
                "id" : self.model.catid,
                "name" : self.model.name
                }

class QuestionResponse(BaseResponse):
    def serialize(self, request=None):
        question = self.model.question
        options = [self.model.var_a.encode("UTF-8"),
                   self.model.var_b.encode("UTF-8"),
                   self.model.var_c.encode("UTF-8"),
                   self.model.var_d.encode("UTF-8")
                   ]
        category_name = self.model.category
        answer = self.model.real_answer
        return  {
                 "id" : self.model.qid,
                 "question" : question,
                 "options" : options,
                 "answer" :answer,
                 "category" : category_name
                }

class Resolve(BaseResponse):
    def serialize(self, request=None):
        return dict()
