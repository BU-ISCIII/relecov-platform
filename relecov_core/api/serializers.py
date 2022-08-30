from rest_framework import serializers

from relecov_core.models import (
    BioInfoAnalysisValue,
    LineageValues,
    Sample,
    Effect,
    VariantAnnotation,
    VariantInSample,
    Filter,
    Variant,
    DateUpdateState,
)


class CreateBioInfoAnalysisValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BioInfoAnalysisValue
        fields = "__all__"


class CreateDateAfterChangeStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DateUpdateState
        fields = "__all__"


class UpdateSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = "__all__"


class CreateSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = "__all__"


class CreateEffectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Effect
        fields = "__all__"


class CreateVariantInSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantInSample
        fields = "__all__"


class CreateVariantAnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantAnnotation
        fields = "__all__"


class CreateFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = "__all__"


class CreateVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = "__all__"


class CreateLineageValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineageValues
        fields = "__all__"
