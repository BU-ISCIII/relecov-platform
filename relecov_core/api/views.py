from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
    action,
    #    parser_classes,
)
from rest_framework import status
from rest_framework.response import Response
from django.http import QueryDict
from relecov_core.api.serializers import (
    CreateSampleSerializer,
    CreateAuthorSerializer,
    CreateGisaidSerializer,
    CreateEnaSerializer
)

from relecov_core.api.utils.long_table_handling import fetch_long_table_data
from .utils.analysis_handling import process_analysis_data
from relecov_core.api.utils.sample_handling import (
    check_if_sample_exists,
    split_sample_data)
from relecov_core.api.utils.bioinfo_metadata_handling import fetch_bioinfo_data

# from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


"""
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
"""


@authentication_classes([SessionAuthentication, BasicAuthentication])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_sample_data(request):
    if request.method == "POST":
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()
        # check if sample is alrady defined
        if "sequencing_sample_id" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if check_if_sample_exists(data["sequencing_sample_id"]):
            error = {"ERROR": "sample already defined"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        data["user"] = request.user.pk
        split_data = split_sample_data(data)
        if "ERROR" in split_data:
            return Response(split_data, status=status.HTTP_400_BAD_REQUEST)

        author_serializer = CreateAuthorSerializer(data=split_data["author"])
        if not author_serializer.is_valid():
            return Response(
                author_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        import pdb
        pdb.set_trace()
        gisaid_serializer = CreateGisaidSerializer(data=split_data["gisaid"])
        if not gisaid_serializer.is_valid():
            return Response(
                gisaid_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        ena_serializer = CreateEnaSerializer(data=split_data["ena"])
        if not ena_serializer.is_valid():
            return Response(
                ena_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        # Store authors, gisaid, ena in ddbb to get the references
        author_serializer.save()
        gisaid_serializer.save()
        ena_serializer.save()
        split_data["sample"]["author_obj"] = author_serializer
        split_data["sample"]["gisaid_obj"] = gisaid_serializer
        split_data["sample"]["ena_obj"] = ena_serializer
        sample_serializer = CreateSampleSerializer(data=split_data["sample"])
        if not sample_serializer.is_valid():
            return Response(
                sample_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        sample_serializer.save()
        return Response("Successful upload information", status=status.HTTP_201_CREATED)


y_param = openapi.Parameter("y", "query", openapi.IN_FORM, type=openapi.TYPE_STRING)

"""
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
"""
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
def bioinfo_metadata_file(request):
    # bioinfo_data = BioInfoProcessValue.objects.all()
    # bioinfo_data.delete()
    if request.method == "POST":
        data = request.data
        # file_received = request.FILES.get("data")

    if isinstance(data, QueryDict):
        data = data.dict()
    stored_data = fetch_bioinfo_data(data)

    if "ERROR" in stored_data:
        return Response(stored_data, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_201_CREATED)
