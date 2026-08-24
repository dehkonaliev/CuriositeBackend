from rest_framework import serializers
from baseapp.utils import field_error


class GetAudioSerializer(serializers.Serializer):
    text_input = serializers.CharField()
    
