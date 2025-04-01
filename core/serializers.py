from rest_framework import serializers
import core.models

class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = core.models.Sample
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

class SampleStateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk')
    label = serializers.CharField(source='display_string')

    class Meta:
        model = core.models.SampleState
        fields = ['id', 'label']


class SampleSearchResultSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="sequencing_sample_id")
    state = serializers.SerializerMethodField()
    sequencing_date = serializers.SerializerMethodField()
    recorded_date = serializers.SerializerMethodField()

    class Meta:
        model = core.models.Sample
        fields = [
            "id",
            "name",
            "state",
            "sequencing_date",
            "recorded_date"
        ]

    def get_state(self, obj):
        return obj.get_state()

    def get_sequencing_date(self, obj):
        return obj.sequencing_date.strftime("%d-%B-%Y") if obj.sequencing_date else ""

    def get_recorded_date(self, obj):
        return obj.created_at.strftime("%d-%B-%Y") if obj.created_at else ""