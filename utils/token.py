# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 22:59
import msgpack
import hmac

from cryptography.fernet import Fernet, InvalidToken
from rest_framework.exceptions import AuthenticationFailed
from django.utils.encoding import force_str,force_bytes
from django_redis import get_redis_connection
from django.contrib.auth import get_user_model
from rest_framework.exceptions import APIException

from Fresh_every_day import settings

User=get_user_model()
redis=get_redis_connection('user')

class Token(object):

    def __init__(self):
        if hasattr(settings,'FERNET_TOKEN'):
            self.token_key=settings.FERNET_TOKEN.get('KEY',None)
        else:raise APIException('服务器必须设置FERNET_TOKEN','settings error')
        self.token_fields=settings.TOKEN_FILEDS

    @property
    def token(self):
        if not hasattr(self,'_token'):
            self._token = Fernet(self.token_key)
        return self._token

    def generate_token(self,create_token_value):
        user_info=msgpack.dumps(create_token_value)
        return force_str(self.token.encrypt(user_info))[::-1]

    def create_token_value(self,user_instance):
        user_info = {'username': user_instance.username}
        user_info['id']=user_instance.id
        for attr in self.token_fields:
                user_info[attr]=getattr(user_instance,attr)
        return user_info

    def check_access_token(self,token):

        if not token:
            raise AuthenticationFailed("未登录")
        token=force_bytes(token[::-1])
        try:
            bytes_user_info=self.token.decrypt(token)
            user_info=msgpack.loads(bytes_user_info,encoding='utf8')
            user=self.check_db_token(user_info,token)
        except InvalidToken:
            raise AuthenticationFailed("登录验证失败")
        except Exception as ex:
            raise ex
            #raise AuthenticationFailed("服务器错误")

        return user,user_info

    def check_db_token(self,user_info,token):
        redis_token=redis.get(Token.get_token_redis_key(user_info))[::-1]
        if not redis_token or not hmac.compare_digest(redis_token,token):
            raise InvalidToken()
        return self.get_user(user_info)

    def get_user(self,user_info):
        try:
            return User.objects.get(is_active=True,id=user_info['id'])
        except:
            raise InvalidToken()

    @staticmethod
    def get_token_redis_key(user_info):
        key=user_info.get('username')
        return force_bytes(':'.join((key,'token')))


token_ins=Token()