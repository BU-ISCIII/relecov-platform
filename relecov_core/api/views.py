from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

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
from relecov_core.api.serializers import CreateSampleSerializer
from relecov_core.models import SampleState

from relecov_core.api.utils.long_table_handling import fetch_long_table_data
from .utils.analysis_handling import process_analysis_data
from relecov_core.api.utils.bioinfo_handling import fetch_bioinfo_data

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
        data["user"] = request.user.pk

        data["state"] = (
            SampleState.objects.filter(state__exact="Defined").last().get_state_id()
        )
        sample_serializer = CreateSampleSerializer(data=data)

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
        if isinstance(data, QueryDict):
            data = data.dict()
        if "analysis" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        fetched_data = process_analysis_data(data)
        if "ERROR" in fetched_data:
            return Response(fetched_data, status=status.HTTP_400_BAD_REQUEST)
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


@api_view(["POST"])
def bioinfo_data(request):
    if request.method == "POST":
        data = request.data
    if isinstance(data, QueryDict):
        data = data.dict()
    fetch_bioinfo_data(data)

    # if "ERROR" in stored_data:
    #    return Response(stored_data, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_201_CREATED)
