from rest_framework import serializers
from engine.models import Leaderboard 
 
class UserSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True, max_length=255)
    ranking = serializers.IntegerField(min_value=0)
    name = serializers.CharField(required=True, max_length=255)
    title = serializers.CharField(required=True, max_length=255)
    avatar = serializers.CharField(required=True, max_length=255)
    city = serializers.CharField(required=True, max_length=255)
    country = serializers.CharField(required=True, max_length=255)
    
    def restore_object(self, attrs, obj=None):
        if obj:
            obj.uid = attrs.get('uid', object.uid)
            obj.ranking = attrs.get('ranking', object.ranking)
            obj.name = attrs.get('name', object.name)
            obj.title = attrs.get('title', object.title)
            obj.avatar = attrs.get('avatar', object.avatar)
            obj.city = attrs.get('city', object.city)
            obj.country = attrs.get('country', object.country)
            return obj
        
        return UserSerializer(
                    attrs.get('uid'),
                    attrs.get('ranking'),
                    attrs.get('name')
                    )
