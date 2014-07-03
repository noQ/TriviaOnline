
from engine.models import User, SocialConnector

class UserManager(object):
    def __init__(self, **kwargs):
        self.user           = None
        self.uid            = None
        
        if kwargs.has_key("uid"):
            uid = kwargs.get("uid")
            if isinstance(uid, basestring):
                if len(uid) > 0:
                    self.uid = uid
                    self.user = self.get_user_by_uid(self.uid)
    
    def get_user_by_uid(self, uid):
        if self.user:
            return self.user
        return User.objects(uid=uid).first()
    
    def get_user_by_id(self, id):
        self.user =  User.objects.with_id(id)
        return self.user
    
    def get_user_by_email(self, email):
        self.user =  User.objects(email=email).first()
        return self.user
    
    def get_users(self, id_list):
        return User.objects(uid__in=id_list).select_related()
    
    
    def get_or_create_social_connector(self, social_link, uid=None):
        if not isinstance(social_link, dict):
            raise Exception("Social Link is not instance of dict")
        if uid is None:
            uid = self.get_uid()
        sconnector = SocialConnector.objects(uid=uid).first()
        if sconnector is None:
            sconnector = SocialConnector(uid=uid, social=social_link)
        else:
            ''' extract key from social connector (dict) '''
            if len(sconnector.social.keys()) > 0:
                search_key = social_link.keys()[0]
                if len(search_key) != 0:
                    ''' update/add key with value '''
                    sconnector.social[search_key] = social_link.get(search_key)
            else:
                sconnector.social.update(social_link)
        sconnector.save()
        return (sconnector.social, sconnector.social.values(), sconnector)
    
    def get_social_connector(self, uid):
        if uid is None:
            uid = self.get_uid()
        sconnector = SocialConnector.objects(uid=uid).first()
        if sconnector:
            return sconnector
        return None
    
    def delete_social_connector(self, uid, type):
        if uid is None:
            uid = self.get_uid()
        sconnector = SocialConnector.objects(uid=uid).first()
        if sconnector is None:
            return None
        if sconnector.social.has_key(type):
            del sconnector.social[type]
            sconnector.save()
        return sconnector.social
        
    def get_user_by_social_id(self, id, platform):
        social_field = "social.%s.id" % platform 
        social_id_lookup = {social_field : id }
        return SocialConnector.objects(__raw__=social_id_lookup).first()
