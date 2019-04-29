# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 22:59
import msgpack
import hmac

from itsdangerous import TimedJSONWebSignatureSerializer as dangerous
from itsdangerous.exc import SignatureExpired,BadSignature
from cryptography.fernet import Fernet, InvalidToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import APIException
from django.utils.encoding import force_str,force_bytes
from django_redis import get_redis_connection
from django.contrib.auth import get_user_model

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
        redis_token=redis.get(Token.get_token_redis_key(user_info))
        if not redis_token or not hmac.compare_digest(redis_token[::-1],token):
            raise InvalidToken()
        return self.get_user(user_info)

    def get_user(self,user_info):
        try:
            return User.objects.get(is_active=True,id=user_info['id'])
        except:
            raise InvalidToken()

    @staticmethod
    def get_token_redis_key(result:dict):
        username=result.get('username')
        return force_bytes(':'.join((username,'token')))

    def delete_db_token(self,redis_key):
        temp=redis.get(redis_key)
        if temp:
            redis.delete(redis_key)
            return True


class ItsDangerousToken(object):
    token=dangerous(settings.SECRET_KEY, settings.ITSDANGEROUSTOKEN['EXPIRS'])

    def encode_token(self,user):
        token=self.token.dumps(user.id)
        return token.decode('utf8')

    def decode_token(self,token):
        try:
            user_id=self.token.loads(token)
        except SignatureExpired:
            raise AuthenticationFailed({'error':'令牌过期'})
        except BadSignature:
            raise AuthenticationFailed({'error':'令牌不正确'})
        user=User.objects.get(id=user_id)
        user.is_email=True
        user.save()
        return user,''


its_dangerous=ItsDangerousToken()
token_ins=Token()