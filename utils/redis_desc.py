# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/31 10:57
from django_redis import get_redis_connection
from rest_framework.exceptions import APIException

from Fresh_every_day import settings
from utils.token import Token
from utils.sms import send_sms

class GenericRedisFunc(object):
    __slots__ = ('redis_name','func','redis')

    def __init__(self,redis):
        if isinstance(redis, str):
            self.redis_name = redis
        else:
            self.func = redis

    def __call__(self,func):
        self.__init__(func)
        return self

    def __get__(self, instance, owner):
        self.redis=self.get_connect_redis()
        from functools import wraps as wrap
        @wrap(self.func)
        def wraps(*args,**kwargs):
            result=self.func(instance,*args,**kwargs)
            self.set_redis_value(instance,result,*args,**kwargs)
            return result
        if {self.func.__name__}&{'data'}:
            result=wraps()
            print('返回property')
            from rest_framework.utils.serializer_helpers import ReturnDict
            result = ReturnDict(result, serializer=instance)
            return result
        print('返回普通方法')
        return wraps

    def get_connect_redis(self):
        if not hasattr(self,'func') or not hasattr(self,'redis_name'):
            raise Exception("请填写要保存的redis的名称")
        return get_redis_connection(self.redis_name)

    def set_redis_value(self,instance,result,*args,**kwargs):
        raise Exception("未实现set_redis_value方法")


class TokenRedisFunc(GenericRedisFunc):

    def set_redis_value(self,instance,result,*args,**kwargs):
        token=result['token']
        if not self.redis.setex(Token.get_token_redis_key(result),settings.TOKEN_EXPIRS,token):
            raise APIException("server error")


class SmsRedisFunc(GenericRedisFunc):

    def set_redis_value(self,instance,result,*args,**kwargs):
        code=result['code']
        if not self.redis.setex(send_sms.get_sms_redis_key(result),settings.SMS_EXPIRS,code):
            raise APIException("server error")
        del result['code']


