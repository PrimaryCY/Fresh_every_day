# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 22:37
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.db.models import Q
from django_redis import get_redis_connection

from utils.token import token_ins
from utils.sms import send_sms

User=get_user_model()
redis=get_redis_connection('user')
class UserModelBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user=User.objects.get(Q(phone=username)|Q(username=username)|Q(email=username))
            phone=user.phone
            code=kwargs.pop('code',None)
            if code:
                res=redis.get(send_sms.get_sms_redis_key({'phone': phone}))
                if res.decode('utf8')in{code}:
                    return user
                else:
                    return
            elif user.check_password(password):
                return user
        except Exception as ex:
            return

class TokenAuthentication(BaseAuthentication):

    def authenticate(self, request):
        token=request.COOKIES.get('token',None)
        if token:
            user,user_token=token_ins.check_access_token(token)
            return user,user_token
        raise AuthenticationFailed('未持有令牌')


