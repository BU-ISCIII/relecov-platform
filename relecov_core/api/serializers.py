from rest_framework import serializers

from relecov_core.models import (
    # BioInfoProcessValue,
    Authors,
    EnaInfo,
    GisaidInfo,
    # Lineage,
    Sample,
    Chromosome,
    Gene,
    Effect,
    VariantInSample,
    Filter,
    Position,
    Variant,
)

"""
class CreateBioInfoProcessValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BioInfoProcessValue
        fields = "__all__"
"""


class CreateAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authors
        fields = "__all__"


class CreateGisaidSerializer(serializers.ModelSerializer):
    class Meta:
        model = GisaidInfo
        fields = "__all__"


class CreateEnaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnaInfo
        fields = "__all__"


class CreateSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = "__all__"


class CreateChromosomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chromosome
        fields = "__all__"


class CreateGeneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        fields = "__all__"


class CreateEffectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Effect
        fields = "__all__"


class CreateVariantInSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantInSample
        fields = "__all__"


class CreateFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = "__all__"


class CreatePositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = "__all__"


class CreateVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = "__all__"


"""
class CreateLineageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lineage
        fields = ["lineage_name"]
"""
