# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 20:08

from django.contrib.auth import get_user_model
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response

from utils.permissions import IsAdminUser
from apps.user.serializer import UserSerializer,LoginSerializer,SmsSerializer
from api.viewsets import ModelViewSet
from api.mixins import CreateModelMixin
from Fresh_every_day import settings


class UserViewSet(ModelViewSet):
    queryset = get_user_model().objects.filter(is_active=True)
    serializer_class = UserSerializer
    #authentication_classes = (IsAdminUser,)


class LoginViewSet(CreateModelMixin,GenericViewSet):
    serializer_class = LoginSerializer
    authentication_classes = ()
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        #response_data = jwt_response_payload_handler(token, user, request)
        headers = self.get_success_headers(serializer.data)
        data = {"success": True, "msg": "登录成功", "data": serializer.data}
        res=Response(data, status=200, headers=headers)
        res.set_cookie('token',
                        serializer.data.get('token'),
                        expires=settings.TOKEN_EXPIRS,
                        httponly=True)
        return res

class SmsViewSet(CreateModelMixin,GenericViewSet):
    serializer_class = SmsSerializer
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        headers = self.get_success_headers(serializer.data)
        data = {"success": True, "msg": "发送成功", "data": serializer.data}
        return Response(data, status=200, headers=headers)
