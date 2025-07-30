from rest_framework import serializers
from .models import PalmOilCount

class PalmOilCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PalmOilCount
        fields = ['id', 'date', 'suitable_count', 'unsuitable_count', 'image', 'status'] 