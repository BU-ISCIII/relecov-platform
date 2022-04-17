from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from rest_framework import status
from rest_framework.response import Response

@api_view(["GET"])
def test(request):
    return Response("Successful upload information", status=status.HTTP_201_CREATED)
