from rest_framework import serializers

from relecov_core.models import Sample, Chromosome


class CreateSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = "__all__"


class CreateChromosmeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chromosome
        fields = "__all__"
