from rest_framework import serializers

from relecov_core.models import Sample

class CreateSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = []
