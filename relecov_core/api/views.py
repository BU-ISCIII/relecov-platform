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

from .utils.request_handling import split_sample_data, prepare_fields_in_sample
from relecov_core.api.utils.long_table_handling import fetch_long_table_data

from .serializers import CreateSampleSerializer

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
        stored_data = fetch_long_table_data(data)
        if "ERROR" in stored_data:
            return Response(stored_data, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_201_CREATED)
