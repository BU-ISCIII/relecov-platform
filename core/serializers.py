from rest_framework import serializers
from core.models import Sample

class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = ["id", "sample_unique_id", "sequencing_sample_id", "created_at"]
