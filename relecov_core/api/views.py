from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FileUploadParser, FormParser

from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
    action,
    parser_classes,
)
from rest_framework import status
from rest_framework.response import Response
from django.http import QueryDict

<<<<<<< HEAD
from .serializers import CreateSampleSerializer, CreateChromosomeSerializer
from relecov_core.models import Chromosome
=======
from .serializers import (
    CreateSampleSerializer,
    CreateChromosomeSerializer,
    CreateGeneSerializer,
    CreateEffectSerializer,
    CreateVariantInSampleSerializer,
    CreateFilterSerializer,
    CreatePositionSerializer,
    # CreateVariantSerializer,
)

from relecov_core.models import (
    # Sample,
    Chromosome,
    Gene,
    Effect,
    VariantInSample,
    Filter,
    Position,
    # Variant,
)
>>>>>>> 2b304a853d2a6c3006399f5d3bb92900ac39177e

from .utils.request_handling import split_sample_data, prepare_fields_in_sample

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

analysis_data = openapi.Parameter(
    "analysis_name",
    openapi.IN_FORM,
    description="Name of the analsys to be performed",
    type=openapi.TYPE_STRING,
)
analysis_file = openapi.Schema(
    "upload_file",
    in_=openapi.IN_BODY,
    type=openapi.TYPE_FILE,
)


@api_view(["GET"])
def test(request):
    return Response("Successful upload information", status=status.HTTP_201_CREATED)


@authentication_classes([SessionAuthentication, BasicAuthentication])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_sample_data(request):
    if request.method == "POST":
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()
        # if "sample" not in data and "project" not in data:
        #    return Response(status=status.HTTP_400_BAD_REQUEST)
        split_data = split_sample_data(data)
        if "ERROR" in split_data:
            return Response(split_data, status=status.HTTP_400_BAD_REQUEST)
        s_data = prepare_fields_in_sample(split_data["sample"])
        if "ERROR" in s_data:
            return Response(s_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        s_data["sampleUser"] = request.user.pk

        sample_serializer = CreateSampleSerializer(data=s_data)

        if not sample_serializer.is_valid():
            return Response(
                sample_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        sample_serializer.save()
        return Response("Successful upload information", status=status.HTTP_201_CREATED)


y_param = openapi.Parameter("y", "query", openapi.IN_FORM, type=openapi.TYPE_STRING)


@parser_classes(
    (
        FormParser,
        MultiPartParser,
        FileUploadParser,
    )
)
@swagger_auto_schema(
    method="post",
    # manual_parameters=[analysis_file],
    request_body=[y_param],
    responses={
        200: "Successful upload information",
        400: "Bad Request",
        500: "Internal Server Error",
    },
)
# @action(detail=True, methods=['post'], parser_classes=(MultiPartParser, ), name='upload-excel', url_path='upload-excel')
@api_view(["POST"])
@action(detail=False, methods=["post"])
def analysis_data(request):
    if request.method == "POST":
        data = request.data
        print(data)
        # if "upload_file" in request.FILES:
        #     a_file = request.FILES["analysis_file"]
        #    print(a_file)

    return Response(status=status.HTTP_201_CREATED)


@api_view(["POST"])
def longtable_data(request):
    if request.method == "POST":
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()
        if Chromosome.objects.filter(chromosome__iexact=data["Chrom"]).exists():
            chrom_id = (
                Chromosome.objects.filter(chromosome__iexact=data["Chrom"])
                .last()
                .get_chromosome_id()
            )
            print(chrom_id)
        else:
            chrom_serializer = CreateChromosomeSerializer(data=data["Chrom"])
            # print(chrom_serializer)
            if chrom_serializer.is_valid():
                chrom_serializer.save()
                print("chrom_serializer saved")

        if Gene.objects.filter(gene__iexact=data["Gene"]).exists():
            gene_id = (
                Gene.objects.filter(gene__iexact=data["Gene"]).last().get_gene_id()
            )
            print(gene_id)
        else:
            gene_serializer = CreateGeneSerializer(data=data["Gene"])
            # print(gene_serializer)
            if gene_serializer.is_valid():
                gene_serializer.save()
                print("gene_serializer saved")

        if Effect.objects.filter(effect__iexact=data["Effect"]).exists():
            effect_id = (
                Effect.objects.filter(effect__iexact=data["Effect"])
                .last()
                .get_effect_id()
            )
            print(effect_id)
        else:
            effect_serializer = CreateEffectSerializer(data=data["Effect"])
            # print(effect_serializer)
            if effect_serializer.is_valid():
                effect_serializer.save()
                print("effect_serializer saved")

        if VariantInSample.objects.filter(dp__iexact=data["VariantInSample"]).exists():
            variant_in_sample_id = (
                VariantInSample.objects.filter(effect__iexact=data["VariantInSample"])
                .last()
                .get_variant_in_sample_id()
            )
            print(variant_in_sample_id)
        else:
            variant_in_sample_serializer = CreateVariantInSampleSerializer(
                data=data["VariantInSample"]
            )
            # print(variant_in_sample_serializer)
            if variant_in_sample_serializer.is_valid():
                variant_in_sample_serializer.save()
                print("variant_in_sample_serializer saved")

        if Filter.objects.filter(filter__iexact=data["Filter"]).exists():
            filter_id = (
                Filter.objects.filter(filter__iexact=data["Filter"])
                .last()
                .get_filter_id()
            )
            print(filter_id)
        else:
            filter_serializer = CreateFilterSerializer(data=data["Filter"])
            # print(filter_serializer)
            if filter_serializer.is_valid():
                filter_serializer.save()
                print("filter_serializer saved")

        if Position.objects.filter(pos__iexact=data["Position"]).exists():
            position_id = (
                Gene.objects.filter(pos__iexact=data["Position"])
                .last()
                .get_position_id()
            )
            print(position_id)
        else:
            position_serializer = CreatePositionSerializer(data=data["Position"])
            # print(position_serializer)
            if position_serializer.is_valid():
                position_serializer.save()
                print("position_serializer saved")
        """
        if Variant.objects.filter(dp__iexact=data["Variant"]).exists():
            variant_id = (
                Variant.objects.filter(effect__iexact=data["Variant"])
                .last()
                .get_variant_id()
            )
            print(variant_id)
        else:
            variant_serializer = CreateVariantSerializer(data=data["Variant"])
            # print(variant_serializer)
            if variant_serializer.is_valid():
                variant_serializer.save()
                print("variant_serializer saved")
        """
        return Response(status=status.HTTP_201_CREATED)
