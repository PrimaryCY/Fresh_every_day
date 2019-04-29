# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/1 21:47

from rest_framework.mixins import CreateModelMixin,ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django.contrib.auth import get_user_model
from rest_framework.decorators import action

from apps.user.serializer import (EmailSerializer,CheckSerializer,
    PersonalUserSerializer,UserAddrSerializer)
from utils.authentication import ItsDangerousAuthentication
from api.mixins import UpdateModelMixin,BulkOperationBaseMixin
from api.viewsets import ModelViewSet
from apps.user.models import UserAddress

User=get_user_model()
class EmailViewSet(CreateModelMixin,GenericViewSet):
    """邮箱修改密码视图"""
    serializer_class =EmailSerializer
    update_serializer_class=CheckSerializer
    authentication_classes = ()
    list_authentication_classes = (ItsDangerousAuthentication,)

    def get_serializer_class(self):
        return self.serializer_class if self.action in {'create'} \
            else self.update_serializer_class

    def create(self, request, *args, **kwargs):
        """发送验证码至邮箱"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        headers = self.get_success_headers(serializer.data)
        data = {"success": True, "msg": "发送成功", "data":serializer.data}
        # from django.shortcuts import redirect
        # return redirect('http://www.baidu.com')
        return Response(data, status=200,headers=headers)

    def list(self,request,*args,**kwargs):
        """校验验证码"""
        data={"success":True}
        return Response(data,status=200)

    def bulk_update(self, request, *args, **kwargs):
        """修改用户密码"""
        serializer = self.get_serializer(request.user,data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        data = {"success": True, "msg": "修改密码成功", "data": serializer.data}
        return Response(data)

    def perform_update(self,serializer):
        serializer.save()

    def get_authenticators(self):
        if self.request.method in {'GET','PUT'}:
            return [temp() for temp in self.list_authentication_classes]
        return [temp() for temp in self.authentication_classes]

class PersonalUserViewSet(ListModelMixin,GenericViewSet):
    """个人用户视图"""
    serializer_class = PersonalUserSerializer
    #lookup_value_regex=r""

    def get_queryset(self):
        return {self.request.user,}

    #@action(methods=['put'],detail=False,url_path='')
    def bulk_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        data = {"success": True, "msg": "修改成功", "data": serializer.data}
        return Response(data)

    def perform_update(self, serializer):
        serializer.save()

class UserAddrViewSet(ModelViewSet):
    queryset = UserAddress.objects.filter(is_active=True)
    serializer_class = UserAddrSerializer
    filter_backends = (SearchFilter,)
    search_fields=('address','signer_name','province')




