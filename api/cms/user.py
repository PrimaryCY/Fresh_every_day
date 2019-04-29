# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 20:08
from django.contrib.auth import get_user_model
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.filters import SearchFilter,OrderingFilter
from rest_framework.exceptions import *
from django_filters.rest_framework import DjangoFilterBackend
from django.db.transaction import atomic

from apps.user.serializer import (UserSerializer,LoginSerializer,SmsSerializer,UserAddrSerializer,
                                  PostDeptSerializer,TreeSerializer,MeanSerializer,RoleSerializer,
                                  UserRolesSerializer,CmsUserRolesSerializer)
from apps.user.models import UserAddress,Department,Tree,Mean,Roles,UserRoles
from api.viewsets import ModelViewSet
from api.mixins import CreateModelMixin,RetrieveModelMixin,UpdateModelMixin,DestroyModelMixin
from Fresh_every_day import settings
from utils.util import CustomLimitOffsetPagination
from api.viewsets import RedisCacheModelViewSet
from utils.token import redis


class UserViewSet(ModelViewSet):
    """所有用户视图"""
    queryset = get_user_model().objects.filter(is_active=True)
    serializer_class = UserSerializer
    filter_backends = (SearchFilter,OrderingFilter,DjangoFilterBackend)
    filter_fields=('gender','is_admin')
    search_fields = ('username', 'phone', 'email')
    ordering_fields = ('update_time', 'create_time')
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        dept_id=self.request.query_params.get('dept_id',None)
        if hasattr(dept_id,'isnumeric') and dept_id.isnumeric():dept_id = int(dept_id)
        if dept_id and dept_id not in set(self.request.dept_ids):
            raise ValidationError({'error':'您没有权限查看该分院下用户'})
        if dept_id:
            dept_id=Department.objects.get(id=dept_id).get_descendants(include_self=True).values_list('id',flat=True)
            return get_user_model().objects.filter(department__in=dept_id)
        else:
            return get_user_model().objects.filter(department__in=self.request.dept_ids)

    @atomic()
    def create(self, request, *args, **kwargs):
        return super().create(request,*args,**kwargs)

    @atomic()
    def update(self, request, *args, **kwargs):
        return super().update(request,*args,**kwargs)

    @atomic()
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request,*args,**kwargs)


class LoginViewSet(CreateModelMixin,GenericViewSet):
    """登录视图"""
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

    def bulk_delete(self,request,*args,**kwargs):
        serializer = self.get_serializer_class()
        serializer.delete(request.user)
        data = {"success": True, "msg": "退出登录"}
        return Response(data, status=200)

    def get_authenticators(self):
        if self.request.method in {'DELETE'}:
            return [temp() for temp in api_settings.DEFAULT_AUTHENTICATION_CLASSES]
        return [temp() for temp in self.authentication_classes]

class SmsViewSet(CreateModelMixin,GenericViewSet):
    """短信视图"""
    serializer_class = SmsSerializer
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        headers = self.get_success_headers(serializer.data)
        data = {"success": True, "msg": "发送成功", "data": serializer.data}
        return Response(data, status=200, headers=headers)


class AllUserAddrViewSet(ModelViewSet):
    """所有用户地址视图"""
    queryset = UserAddress.objects.filter(is_active=True)
    serializer_class = UserAddrSerializer
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    filter_fields = ('user','province','city')
    search_fields = ('address', 'signer_mobile')
    ordering_fields = ('update_time', 'create_time')
    pagination_class = CustomLimitOffsetPagination


class DepartmentViewSet(RedisCacheModelViewSet):
    """部门视图"""
    serializer_class = PostDeptSerializer
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    filter_fields = ('id', 'level')
    search_fields = ('name',)
    ordering_fields = ('update_time', 'create_time')
    redis=redis
    redis_result_key = redis_key = 'Department'

    def get_queryset(self):
        return self.request.role.department.get_descendants(include_self=True).filter(is_active=True) \
            if self.request.role.department_id else Department.objects.filter(is_active=True)

    def get_list_queryset(self):
        return self.request.role.department

    def perform_destroy(self, instance):
        instance.get_descendants(include_self=True).update(is_active=False)

    def get_redis_key(self):
        return self.redis_key

    class RedisMeta:
        model=Department
        redis_fields=('id','parent_id','name','level','desc','is_active')


class TreeViewSet(ModelViewSet):
    queryset = Tree.objects.all()
    serializer_class = TreeSerializer

class MeanViewSet(RedisCacheModelViewSet):
    """菜单视图"""
    serializer_class = MeanSerializer
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    filter_fields = ('id', 'level')
    search_fields = ('name',)
    ordering_fields = ('update_time', 'create_time')
    redis = redis
    redis_result_key = redis_key= 'Mean'

    def get_queryset(self):
        return self.request.role.role.button.all()

    def perform_destroy(self, instance):
        instance.get_descendants(include_self=True).update(is_active=False)

    def get_list_query(self):
        return self.request.role.button.all()

    class RedisMeta:
        model=Mean
        redis_fields = ('id', 'parent_id', 'name', 'level', 'desc','is_active')


class RoleViewSet(ModelViewSet):
    """角色管理视图"""
    queryset = Roles.objects.all()
    serializer_class = RoleSerializer

    def get_queryset(self):
        return Roles.objects.filter(is_active=True,department__in=self.request.dept_ids).all()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
        instance.userroles__set().update(is_active=False)


class UserRoleViewSet(ListModelMixin,UpdateModelMixin,GenericViewSet):
    """切换角色视图"""

    serializer_class = UserRolesSerializer

    def get_queryset(self):
        return UserRoles.objects.filter(is_active=True).all()

class CmsRoleViewSet(ModelViewSet):
    """cms设置用户角色"""
    serializer_class =CmsUserRolesSerializer
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    filter_fields = ('user_id',)

    def get_queryset(self):
        return UserRoles.objects.filter(department__in=self.request.dept_ids).all()

    def perform_create(self, serializer):
        user=serializer.save().user
        if not user.is_admin:
            user.is_admin=True
            user.save()



