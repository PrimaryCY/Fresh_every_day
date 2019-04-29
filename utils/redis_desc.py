# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/31 10:57
import json
import numba
import re
from functools import wraps as wrap
from collections import Iterable
import simdjson

from django_redis import get_redis_connection
from rest_framework.exceptions import APIException,ValidationError
from django.utils.functional import cached_property
from rest_framework.serializers import Serializer
from rest_framework.utils.serializer_helpers import ReturnDict,ReturnList
from rest_framework_extensions.cache.decorators import available_attrs
from rest_framework.response import Response

from Fresh_every_day import settings
from utils.token import Token
from utils.sms import Sms
from apps.user.celery import send_sms
from apps.user.models import Department
from utils.util import SetJsonEncoder


class GenericRedisFunc(object):
    __slots__ = ('redis_name','func','_redis')

    def __init__(self,redis):
        if isinstance(redis, str):
            self.redis_name = redis
        else:
            self.func = redis

    def __call__(self,func):
        self.__init__(func)
        return self

    def __get__(self, instance, owner):
        @wrap(self.func,assigned=available_attrs(self.func))
        def wraps(*args,**kwargs):
            if hasattr(self,'inspect_attr'):
                status=getattr(self,'inspect_attr')(instance,owner,*args,**kwargs)
                if status:
                    print('走的缓存')
                    function=getattr(self, 'get_redis_value')()
                    if function: return function
            result=self.func(instance,*args,**kwargs)
            self.set_redis_value(instance,result,*args,**kwargs)
            result = self.validate_result(result, instance)
            return result
        if self.func.__name__=='data':
            print('返回property')
            return ReturnDict(wraps(), serializer=instance)
        print('返回普通方法')
        return wraps

    @cached_property
    def redis(self):
        if not hasattr(self,'_redis'):
            self._redis=self.get_connect_redis()
        return self._redis

    def get_connect_redis(self):
        if not hasattr(self,'func') or not hasattr(self,'redis_name'):
            raise Exception("请填写要保存的redis的名称")
        return get_redis_connection(self.redis_name)

    def set_redis_value(self,instance,result,*args,**kwargs):
        raise Exception("未实现set_redis_value方法")

    def validate_result(self,result,instance:Serializer):
        if hasattr(instance,self.get_result()):
            return getattr(instance,self.get_result())(result)
        return result

    def get_result(self):
        return f'get_{self.func.__name__}'


class TokenRedisFunc(GenericRedisFunc):

    def set_redis_value(self,instance,result,*args,**kwargs):
        token=result['token']
        if not self.redis.setex(Token.get_token_redis_key(result),settings.TOKEN_EXPIRS,token):
            raise APIException("server error")


class SmsRedisFunc(GenericRedisFunc):

    def set_redis_value(self,instance,result,*args,**kwargs):
        code=result['code']
        if self.redis.get(Sms.get_sms_redis_key(result)):
            raise ValidationError({'error':"已经发送过手机验证码了"})
        elif not self.redis.setex(Sms.get_sms_redis_key(result),settings.SMS_EXPIRS,code):
            raise APIException("server error")
        self.send_celery_sms(result)
        del result['code']

    def send_celery_sms(self,result):
        mobile=result.get('phone')
        code=result.get('code')
        SMS_CONF=settings.SMS_CONF
        send_sms.delay(SMS_CONF,mobile, code)

#
# class EmailRedisFunc(GenericRedisFunc):
#
#     def set_redis_value(self,instance,result,*args,**kwargs):
#         code=result['code']
#         if not self.redis.setex(self.get_email_redis_key(result),settings.EMAIL_EXPIRS,code):
#             raise APIException("server error")
#         self.send_celery_email(result)
#         del result['code']
#
#     def send_celery_email(self,result):
#         if  self.redis.get(self.get_email_redis_key(result)):
#             raise ValidationError({'error':"已经发送过邮件验证码了"})
#         email=result.get('email')
#         code=result.get('code')
#         send_email.delay(email, code)
#
#     @staticmethod
#     def get_email_redis_key(result):
#         key = result.get('email')
#         return force_bytes(':'.join((key, 'code')))


class GenericViewCache(object):
    """缓存装饰器"""

    def __init__(self,view_cls=None):
        self.view_cls=view_cls

    def __call__(self,func, *args, **kwargs):
        this=self
        @wrap(func, assigned=available_attrs(func))
        def wraps(self,request,*args,**kwargs):
            return this.cache_response(func,self,request,*args,**kwargs)
        return wraps

    def cache_response(self,func,view,request,*args,**kwargs):
        self.view= view
        self.initial(func,view,request,*args,**kwargs)
        return getattr(self,request.method.lower())(func,view,request,*args,**kwargs)

    def initial(self,func,view,request,*args,**kwargs):
        """初始化"""
        # if not request.user:
        #     print('没有用户')
        #     return self.finalize_response(func,view,request,*args,**kwargs)
        #print('有用户')
        self.redis_key=view.get_redis_key()
        self.redis=view.get_redis()
        if not self.FLAG:
            self.FLAG=False

    def get_view_cls(self):
        return self.view_cls or self.view.__class__

    @property
    def FLAG(self):
        if not hasattr(self.get_view_cls(), 'FLAG'):
            self.FLAG = False
        return getattr(self.get_view_cls(), 'FLAG')

    @FLAG.setter
    def FLAG(self, bool=False):
        setattr(self.get_view_cls(), 'FLAG', bool)

    def get(self,view_func,view_instance,request,*args,**kwargs):
        return getattr(self,view_instance.action.lower())(view_func,view_instance,request,*args,**kwargs)

    def __getattr__(self, item):
        if item in ['put','patch','delete','post']:
            return self.template
        return super().__getattribute__(item)

    def template(self,view_func,view_instance,request,*args,**kwargs):
        raise APIException('未实现模板方法')

    @property
    def query_params(self):
        query_params = [v for k, v in self.view.request.query_params.items() if v.strip() != '' and k != 'format']
        return query_params

    def finalize_response(self,view_func,view_instance,request,*args,**kwargs):
        return view_func(view_instance, request, *args, **kwargs)

    @property
    def Meta(self):
        return self.view.RedisMeta

class RedisCache(GenericViewCache):

    def list(self,view_func,view_instance,request,*args,**kwargs):
        raw_queryset = view_instance.get_queryset()
        if not self.query_params:
            print('没有get参数')
            raw_queryset=view_instance.get_list_queryset()#获取List时的queryset
            return self.list_retrieve_func(view_instance, request, raw_queryset, *args, **kwargs)
        #过滤使用原始的queryset
        print('有get参数')
        queryset = view_instance.filter_queryset(raw_queryset)
        return self.list_retrieve_func(view_instance,request,queryset,*args,**kwargs)

    def retrieve(self,view_func,view_instance,request,*args,**kwargs):
        instance = view_instance.get_object()
        return self.list_retrieve_func(view_instance,request,instance,*args,**kwargs)

    def list_retrieve_func(self,view_instance,request,queryset,*args,**kwargs):
        if not self.FLAG:
            print('重新生成数据')
            init_data = self.initial_data()
            self.set_response(init_data)
            print('生成完毕')

        res=self.get_response(queryset)#,request=request)
        res=self.check_data(res,view_instance)
        response =Response(res,status=200)
        return response



    def check_data(self,res,view_instance):
        if hasattr(view_instance,'get_result'):
            return getattr(view_instance,'get_result')(res)
        return res

    def template(self,view_func,view_instance,request,*args,**kwargs):
        self.FLAG=False
        print('修改了',self.FLAG)
        return self.finalize_response(view_func,view_instance,request,*args,**kwargs)


    def get_response(self, queryset,*args,**kwargs):
        view_kwargs=self.view.kwargs.get(self.view.lookup_url_kwarg or self.view.lookup_field,None)
        res = {self.view.redis_result_key: []}
        raw_data=self.get_raw_redis_value()
        # if not kwargs['request'].role.department_id and not view_kwargs \
        #         and not self.query_params:
        #     print('获取了redis原始数据')
        #     res[self.view.redis_result_key]=(x for x in json.loads(raw_data))
        #     return res
        """
        1.菜单多个子id
        2.菜单只有父id
        3.菜单子id父id混合
        4.部门子id 
        5.搜索筛选出来的子id
        """
        if isinstance(queryset,Iterable):
            a=set()
            for i in queryset.order_by('level').iterator():
                if i.id in a :
                    print(f'跳过{i}')
                    continue
                print(f'执行{i}')
                a=a|set(i.get_family().values_list('id',flat=True))
                res[self.view.redis_result_key].append(self.process_tree_body(i,raw_data))
        else:
            #只是retrieve时候使用这个
            res[self.view.redis_result_key].append(self.process_tree_body(queryset,raw_data))
        res[self.view.redis_result_key]=self.process_tree_ancestors(res[self.view.redis_result_key])
        print('获取了redis处理数据')

        return res


    def process_tree_ancestors(self,res):
        """获取父级id,传入父id即显示拥有所有子id,传入子id会将父id求出来显示"""
        if len(res)>1:
            father = {}
            for i in res:
                father.setdefault(i['parent_id'],[])
                father[i['parent_id']].append(i)
                if i['id'] in father:
                    father.pop(i['id'])
            wondelful_result=[]
            for k,v in father.items():
                if not k:
                    wondelful_result.append(v)
                    continue
                ancestors=self.Meta.model.objects.get(id=k).get_ancestors(include_self=True).values(*self.Meta.redis_fields)
                print('k',k)
                for index,i in enumerate(ancestors):
                    try:
                        i['child']=ancestors[index+1]
                        del i
                    except IndexError:
                        i['child']=v
                        wondelful_result.append(ancestors[0])
            return wondelful_result
        return res

    def process_tree_body(self,instance,data):
        """处理数据"""
        matching_data=re.search(f'{{"id": {instance.id},.*"stop": {instance.id}}}',data)
        if matching_data:
            child_data=json.loads(matching_data.group())
            child_data['pick']=True
            return child_data

    # def process_tree_body(self,instance,data):
    #     """处理数据"""
    #     if not instance.parent_id:
    #         return data
    #     matching_data=re.search(f'{{"id": {instance.parent_id},.*"stop": {instance.parent_id}}}',data)
    #     if matching_data:
    #         import pandas
    #         child_data=pandas.read_json(matching_data.group(),typ='series')
    #         for  i in child_data['child']:
    #             if i['id']==i.id:
    #                 continue
    #             child_data['child'].remove(i)
    #         #child_data['pick']=True
    #         return child_data

    def get_raw_redis_value(self):
        return self.redis.get(self.redis_key).decode()

    def initial_data(self):
        """初始化数据"""
        init = {}
        for i in self.Meta.model.objects.filter(is_active=True).order_by('id')\
                .values(*self.Meta.redis_fields).iterator() :
            init[i['id']] = i
            i.setdefault('child', [])
            i['stop']=i['id']
        res = []
        for k, v in init.items():
            if v.get('parent_id'):
                init[v['parent_id']]['child'].append(v)
            else:
                res.append(v)
            del k,v
        return res

    def set_response(self,initial_data):
        self.FLAG=True
        return self.redis.set(self.redis_key,json.dumps(initial_data,cls=SetJsonEncoder))

