from rest_framework import serializers
import core.models


class SampleCountByStateSerializer(serializers.Serializer):
    label = serializers.CharField(source="state_id__state")
    count = serializers.IntegerField()


class LabUserAssignSerializer(serializers.Serializer):
    labs = serializers.ListField(child=serializers.CharField())
    users = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )
    SUCCESS = serializers.CharField(allow_null=True, required=False)
    ERROR = serializers.CharField(allow_null=True, required=False)

    # FIXME: success and errors shouldnt be added here.
    @classmethod
    def from_raw_data(cls, labs, users, SUCCESS=None, ERROR=None):
        # Transform users from list of lists → list of dicts
        users_data = [{"id": str(user[0]), "name": user[1]} for user in users]

        data = {
            "labs": labs,
            "users": users_data,
            "success": SUCCESS,
            "ERROR": ERROR,
        }
        serializer = cls(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.data


class MetadataValueSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="schema_property.label")
    value = serializers.CharField()

    class Meta:
        model = core.models.MetadataValues
        fields = ["label", "value"]


class SampleStateHistorySerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    is_current = serializers.BooleanField()

    class Meta:
        model = core.models.SampleStateHistory
        fields = ["state", "date", "is_current"]

    def get_state(self, obj):
        return obj.get_state()

    def get_date(self, obj):
        return obj.get_date()


class PublicDatabaseValueSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="public_database_fieldID.label_name")
    value = serializers.CharField(allow_blank=True, allow_null=True)

    class Meta:
        model = core.models.PublicDatabaseValues
        fields = ["label", "value"]


class LineageValueSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="lineage_fieldID.lineage_property_name")
    value = serializers.CharField(source="get_value")

    class Meta:
        model = core.models.LineageValues
        fields = ["label", "value"]

class SampleDisplaySerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    gisaid = serializers.SerializerMethodField()
    ena = serializers.SerializerMethodField()
    bioinfo = serializers.SerializerMethodField()
    lineage = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    lab = serializers.SerializerMethodField()

    class Meta:
        model = core.models.Sample
        fields = [
            "id",
            "sample_unique_id",
            "sequencing_sample_id",
            "created_at",
            "state",
            "user",
            "lab",
            "actions",
            "bioinfo",
            "gisaid",
            "ena",
            "lineage",
        ]

    def get_state(self, obj):
        return obj.get_state()

    def get_user(self, obj):
        return str(obj.user) if obj.user else None

    def get_lab(self, obj):
        return obj.get_collecting_institution()

    def get_actions(self, obj):
        return SampleStateHistorySerializer(self.context.get("actions_qs", []), many=True).data

    def get_gisaid(self, obj):
        return PublicDatabaseValueSerializer(self.context.get("gisaid_qs", []), many=True).data

    def get_ena(self, obj):
        return PublicDatabaseValueSerializer(self.context.get("ena_qs", []), many=True).data

    def get_bioinfo(self, obj):
        return MetadataValueSerializer(self.context.get("bioinfo_qs", []), many=True).data

    def get_lineage(self, obj):
        return LineageValueSerializer(self.context.get("lineage_qs", []), many=True).data


#############################


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


class PublicAccessionSerializer(serializers.Serializer):
    lab_name = serializers.CharField()
    sample_name = serializers.CharField()
    accession_id = serializers.CharField()

    @classmethod
    def from_raw(cls, raw_tuples):
        return [cls({ "lab_name": tup[0], "sample_name": tup[1], "accession_id": tup[2]}).data for tup in raw_tuples]


class LabLastActionSerializer(serializers.Serializer):
    lab = serializers.CharField()
    defined = serializers.CharField(allow_blank=True)
    analysis = serializers.CharField(allow_blank=True)
    gisaid = serializers.CharField(allow_blank=True)
    ena = serializers.CharField(allow_blank=True)

    @classmethod
    def from_raw(cls, raw_list):
        keys = ["lab", "defined", "analysis", "gisaid", "ena"]
        return [cls(dict(zip(keys, entry))).data for entry in raw_list]


class LabLastActionDictSerializer(serializers.Serializer):
    Defined = serializers.CharField(allow_blank=True, required=False)
    Analysis = serializers.CharField(allow_blank=True, required=False)
    Gisaid = serializers.CharField(allow_blank=True, required=False)
    Ena = serializers.CharField(allow_blank=True, required=False)

    @classmethod
    def from_raw(cls, raw_dict):
        return cls(raw_dict).data
