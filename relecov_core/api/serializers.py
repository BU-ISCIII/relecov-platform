from rest_framework import serializers

from relecov_core.models import (
    BioinfoAnalysisValue,
    DateUpdateState,
    Effect,
    Filter,
    LineageValues,
    Sample,
    Variant,
    VariantAnnotation,
    VariantInSample,
    PublicDatabaseValues,
)


class CreateBioinfoAnalysisValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BioinfoAnalysisValue
        fields = "__all__"


class CreateDateAfterChangeStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DateUpdateState
        fields = "__all__"


class CreateSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = "__all__"


class CreateEffectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Effect
        fields = "__all__"


class CreateErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
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


class CreatePublicDatabaseValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicDatabaseValues
        fields = "__all__"


class UpdateStateSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = "__all__"
