# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/6 12:49
import json
import datetime
from datetime import date
from functools import wraps

from rest_framework.pagination import LimitOffsetPagination
from rest_framework_extensions.cache.decorators import available_attrs
from rest_framework.fields import ChoiceField
from django.db.models import Model

from apps.user.models import Department


class CustomLimitOffsetPagination(LimitOffsetPagination):
    #默认显示的个数
    default_limit = 2
    #当前的位置
    offset_query_param = "offset"
    #通过limit改变默认显示的个数
    limit_query_param = "limit"
    #一页最多显示的个数
    max_limit = 10

class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)

class SetJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)

class CustomChoiceFiled(ChoiceField):

    def to_representation(self, value):
        return self.choices.get(value)


def sort_queryset(model,list,sort_field='id'):
    assert issubclass(model,Model),(
        '传入的不是ModelClass'
    )
    queryset=[]
    if list:
        sku_ids = ','.join([str(i) for i in list])
        field_sql = f"FIELD(`{sort_field}`,{sku_ids})"
        queryset = model.objects.extra(select={'field_sql': field_sql},where=[f'id IN ({sku_ids})'],
                                  order_by=['field_sql'])
    return queryset



class RedisTranscaction(object):
    __slots__ = ('func',)

    def __init__(self,func):
        self.func = func

    def __call__(self,func):
        return self

    def __get__(self, instance, owner):
        @wraps(self.func,assigned=available_attrs(self.func))
        def wrap(*args,**kwargs):
            print('使用事务了')
            instance.redis= instance.redis.pipeline(transaction=True)
            instance.redis.multi()
            result=self.func(instance,*args,**kwargs)
            instance.redis.execute()
            return result
        return wrap