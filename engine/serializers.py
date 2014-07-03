from rest_framework import serializers
from models import User, Session, Leaderboard

class UserSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True, max_length=255)
    ranking = serializers.IntegerField(min_value=0)
    name = serializers.CharField(required=True, max_length=255)
    title = serializers.CharField(required=True, max_length=255)
    avatar = serializers.CharField(required=True, max_length=255)
    city = serializers.CharField(required=True, max_length=255)
    country = serializers.CharField(required=True, max_length=255)
    
    def restore_object(self, attrs, obj=None):
        print str(attrs)
        if obj:
            obj.uid = attrs.get('uid', object.uid)
            obj.ranking = attrs.get('ranking', object.ranking)
            obj.name = attrs.get('name', object.name)
            obj.title = attrs.get('title', object.title)
            obj.avatar = attrs.get('avatar', object.avatar)
            obj.city = attrs.get('city', object.city)
            obj.country = attrs.get('country', object.country)
            return obj
        
        return User(
                    attrs.get('uid'),
                    attrs.get('ranking'),
                    attrs.get('name')
                    )
    

class LeaderboardSerializer(serializers.Serializer):
    uid   = serializers.CharField(required=True)
    full_name  = serializers.CharField(required=True)
    score = serializers.IntegerField(min_value=0)
    place = serializers.IntegerField(min_value=0)

    def restore_object(self, attrs, obj=None):
        print str(attrs)
        if obj:
            obj.uid = attrs.get('uid', object.uid)
            obj.full_name = attrs.get('full_name', object.full_name)
            obj.score = attrs.get('score', object.score)
            obj.place = attrs.get('place', object.place)
            return obj
        
        return Leaderboard(
                    attrs.get('uid'),
                    attrs.get('full_name'),
                    attrs.get('score'),
                    attrs.get('place')
                    )

class SessionSerializer(serializers.Serializer):
    #name = serializers.CharField(required=True, max_length=255)
    status = serializers.IntegerField(required=True, min_value=0)
    #players = serializers.ChoiceField(required=False)
    
    def restore_object(self, attrs, obj=None):
        print obj
        if obj:
            #obj.name = attrs.get('name', obj.name)
            obj.status = attrs.get('status', obj.status)
            #obj.players = attrs.get('players', object.players)
            return obj
        
        return Session(
                        #attrs.get('name'),
                        attrs.get('status')
                        #attrs.get('players')
                        )
         
