from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from rest_framework import status
from rest_framework.response import Response
from django.http import QueryDict

from .serializers import CreateSampleSerializer

from .utils.request_handling import split_sample_data, prepare_fields_in_sample


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
