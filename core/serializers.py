from rest_framework import serializers
from core.models import Sample

class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = ["id", "sample_unique_id", "sequencing_sample_id", "created_at"]

class UserInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()

class LabUserDataSerializer(serializers.Serializer):
    labs = serializers.ListField(child=serializers.CharField())
    users = UserInfoSerializer(many=True)

    @classmethod
    def from_raw_data(cls, data):
        """Generate serializable structure."""
        formatted_data = {
            "labs": data.get("labs", []),
            "users": [{"id": u[0], "username": u[1]} for u in data.get("users", [])]
        }
        return cls(formatted_data).data
