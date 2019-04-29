from __future__ import unicode_literals

from functools import update_wrapper
from inspect import getmembers

from django.utils.decorators import classonlymethod
from django.views.decorators.csrf import csrf_exempt
from api.mixins import RetrieveModelMixin, UpdateModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins

from utils.redis_desc import RedisCache


class ModelViewSet(CreateModelMixin,
                   RetrieveModelMixin,
                   UpdateModelMixin,
                   DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):

    pass

class RedisCacheModelViewSet(ModelViewSet):
    redis_key=None              #存入reid的key名
    redis=None                  #使用哪个redis实例
    redis_result_key=None       #返回的数据字典key名

    def get_redis(self):
        return self.redis

    def get_redis_key(self):
        return self.redis_key

    def get_list_queryset(self):
        """获取list时redis处理的queryset"""
        return self.get_queryset()

    @RedisCache()
    def create(self, request, *args, **kwargs):
        return super().create(request,*args,**kwargs)
    @RedisCache()
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @RedisCache()
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @RedisCache()
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @RedisCache()
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @RedisCache()
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    class RedisMeta:
        model=None#初始化使用哪个Model
        fields=None#序列化哪几个字段

class ReadOnlyModelViewSet(RetrieveModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """
    pass
