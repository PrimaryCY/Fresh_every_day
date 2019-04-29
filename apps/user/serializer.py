# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 20:08
import re
from random import choice

from django.contrib.auth import get_user_model,authenticate
from django.db import transaction
from django.db.models import Q,F
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import _reverse
from rest_framework.fields import empty

from utils.token import token_ins,its_dangerous
from utils.redis_desc import TokenRedisFunc,SmsRedisFunc
from apps.user.celery import send_email
from Fresh_every_day import settings
from apps.user.models import UserAddress,Department,Tree,Mean,Roles,UserRoles


User=get_user_model()

class UserSerializer(serializers.ModelSerializer):
    signer_password=serializers.CharField(label='请重复输入密码',required=True,write_only=True)
    last_login=serializers.BooleanField(read_only=True,label='最后登录时间')
    is_email=serializers.ReadOnlyField(label='是否邮箱验证')
    is_phone=serializers.ReadOnlyField(label='是否手机验证')
    password=serializers.CharField(style={'input_type': 'password'},write_only=True,label='密码')
    user_addr = serializers.SerializerMethodField()
    roles=serializers.SerializerMethodField(label='用户角色')
    department=serializers.StringRelatedField(label='所属部门')
    is_admin=serializers.HiddenField(default=False)

    def get_roles(self,obj):
        return obj.roles_set.filter(is_active=True).values('id','name')

    def validate_department(self,attr):
        role_dept=attr.id
        if role_dept:
            dept_ids=self.context['request'].dept_ids
            if role_dept not in dept_ids:
                raise ValidationError({'error':'您没有权限设置角色到该单位'})
        return attr

    def validate(self, attrs):
        if not attrs['signer_password']==attrs['password']:
            raise ValidationError('两次输入密码不一致')
        del attrs['signer_password']
        if re.match(settings.REGEX_MOBILE,attrs['username']):
            raise ValidationError('不可以使用手机号码作为用户名')
        return attrs

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.context['view'].basename == 'user_address':del self.fields['user_addr']
        if self.context['view'].action in{'create','update'}:
            self.fields['department']=serializers.PrimaryKeyRelatedField(
                queryset=Department.objects.filter(id__in=self.context['request'].dept_ids),
                label='用户所属部门')

    def get_user_addr(self,user):
        if self.context.get('parent',None):
            return UserAddress.objects.filter(~Q(id=self.context['addr'])&Q(user=user)).values()
        return UserAddress.objects.filter(is_active=True, user=user).values()

    class Meta:
        model=User
        exclude=('created_time','update_time','is_active')


class LoginSerializer(serializers.Serializer):
    username=serializers.CharField(label='用户名',write_only=True)
    password=serializers.CharField(label='密码',write_only=True,required=False)
    code=serializers.CharField(label='验证码',write_only=True,required=False)
    user=serializers.ReadOnlyField()
    token=serializers.ReadOnlyField()
    token_ins=token_ins

    @property
    def username_field(self):
        try:
            self.modelssss = get_user_model()
            username_field = get_user_model().USERNAME_FIELD
        except:
            username_field = 'username'
        return username_field

    @TokenRedisFunc('user')
    def validate(self, attrs):
        user_input = {
            self.username_field: attrs.get(self.username_field),
            'password': attrs.get('password'),
            'code':attrs.get('code')
        }
        if all({user_input.get(self.username_field),
                user_input.get('password')or user_input.get('code')}):
            user = authenticate(**user_input)

            if user:
                if not user.is_active:
                    raise serializers.ValidationError('登录失败,账户不存在')
                payload = self.token_ins.create_token_value(user)
                return {
                    'token': self.token_ins.generate_token(payload),
                    'username': user.username,
                }
            raise serializers.ValidationError('用户名或密码错误')
        else:
            raise serializers.ValidationError('请输入用户名和密码/验证码')

    @classmethod
    def delete(cls,instance):
        redis_key=cls.token_ins.get_token_redis_key({'username':instance.username})
        access=cls.token_ins.delete_db_token(redis_key)
        if not access:
            raise ValidationError({'error':'未知错误'})


class SmsSerializer(serializers.Serializer):
    phone = serializers.CharField(label='手机号码', write_only=True,max_length=11,
                                  min_length=11,required=True,
                                  error_messages={'max_length': '手机号码过长',
                                                  'min_length': '手机号码过短',
                                                  'blank': '手机号码不能为空'})

    def validated_phone(self,phone):
        if not re.match(settings.REGEX_MOBILE, phone):
            raise ValidationError('请输入正确手机号码')
        return phone


    @SmsRedisFunc('user')
    def validate(self, attrs):
        mobile = attrs.get('phone')
        attrs['code'] = code = self.generate_code()
        return attrs

    def generate_code(self):
        seeds = "1234567890"
        random_str = []
        for i in range(4):
            random_str.append(choice(seeds))
        return "".join(random_str)


class EmailSerializer(serializers.Serializer):
    username=serializers.CharField(max_length=100,label='请输入用户名',
                                   required=True,write_only=True)


    def validate(self, attrs):
        try:
            user=User.objects.get(username=attrs['username'])
        except:
            raise ValidationError({'error':'用户名错误'})
        if not user.email:
            raise  ValidationError("该用户没有输入邮箱")

        itsdangerous=its_dangerous.encode_token(user)
        # playload=token_ins.create_token_value(user)
        # token=token_ins.generate_token(playload)

        # 生成绝对url
        url=self.generate_abs_url()
        abs_url='?token='.join([url,itsdangerous])
        send_email.delay(user.email,abs_url)

        return {
            'token': itsdangerous,
            'username': attrs['username'],
        }

    def generate_abs_url(self):
        url = _reverse('email-list', request=self.context['request'])
        return url

    def get_validate(self,result):
        del result['token']
        return result

class CheckSerializer(serializers.Serializer):
    password=serializers.CharField(label='密码',write_only=True)
    check_password=serializers.CharField(label='请确认输入密码',write_only=True)
    username=serializers.ReadOnlyField(label='用户名')

    def validate(self, attrs):
        if not attrs['password'] == attrs['check_password']:
            raise ValidationError({'error':'两次密码输入不一致'})
        return attrs

    # def update(self, instance, validated_data):
    #     instance.set_password(validated_data['password'])
    #     instance.save()
    #     return instance


class PersonalUserSerializer(serializers.ModelSerializer):
    is_email=serializers.ReadOnlyField()
    is_phone=serializers.ReadOnlyField()
    is_admin=serializers.ReadOnlyField()
    last_login=serializers.ReadOnlyField()

    class Meta:
        model=User
        exclude=("password",'is_active')


class UserAddrSerializer(serializers.ModelSerializer):
    user=serializers.HiddenField(default=serializers.CurrentUserDefault(),
                                        source='user.phone')
    is_active=serializers.HiddenField(default=True)
    user_info=serializers.SerializerMethodField()
    default_addr=serializers.BooleanField(allow_null=True,label='是否默认收货地址')
    zip_code=serializers.CharField(max_length=10,min_length=6,label="邮政编码")

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.context['view'].basename in {'all_user_address'}:
            self.fields['user']=serializers.PrimaryKeyRelatedField(required=True,queryset=User.objects.all(),
                                                                   write_only=True,label='用户名')

    def get_user_info(self,obj):
        self.context['addr']=obj.id
        self.context['parent']=self
        instance=UserSerializer(obj.user,many=False,read_only=True,source='user',context=self.context)
        return instance.data

    def validate_default_addr(self,attr):
        if attr:
            return attr
        count=UserAddress.objects.filter(user=self.context['request'].user).count()
        if count == 0:
            return True

    def validate(self, attrs):
        #attrs['user']=attrs['user']['phone']
        return attrs

    class Meta:
        model=UserAddress
        fields="__all__"
        #dept=2


class PostDeptSerializer(serializers.ModelSerializer):

    def __init__(self,instance=None,data=empty ,**kwargs):
        super().__init__(instance,data, **kwargs)
        if hasattr(self.context['request'],'role') and hasattr(self.context['request'].role,'department'):
            if  self.context['request'].role.department:
                id_lis = self.context['request'].dept_ids
                attr={'queryset':Department.objects.filter(Q(id__in=id_lis)&Q(is_active=True)),
                'required':True}
            else:
                attr = {'queryset': Department.objects.filter(is_active=True),
                        "allow_null":True}
            self.fields['parent']=serializers.PrimaryKeyRelatedField(**attr)


    class Meta:
        model=Department
        fields=("id","name","parent","level")



class TreeSerializer(serializers.ModelSerializer):
    xx=serializers.SerializerMethodField()

    def get_xx(self,obj):
        from mptt.utils import get_cached_trees
        # from mptt.models import
        #return Tree.objects.tree.all()
        #Tree.objects.delay_mptt_updates()
        #t=Tree.objects.get_queryset_ancestors(Tree.objects.all())
        return Tree.objects.get_queryset_descendants(Tree.objects.filter(id=obj.id)).values_list()
        #return list(Tree.objects.get_queryset_ancestors(Tree.objects.filter(id=obj.id)).values())
        # return list(t.values())
        # return  Tree.objects.all().get_children()
    class Meta:
        model=Tree
        fields=('id',)


class MeanSerializer(serializers.ModelSerializer):

    class Meta:
        model=Mean
        fields=("id","name","desc","parent","level")

class RoleSerializer(serializers.ModelSerializer):
    created_user=serializers.HiddenField(default=serializers.CurrentUserDefault())
    department=serializers.ListField(label='角色所属分院')

    def validate_department(self,attr):
        attr=set(attr)
        dept_ids=self.context['request'].dept_ids
        if attr-set(dept_ids):
            raise ValidationError({'error':'设置角色所属分院超出权限'})
        #attr=Department.objects.filter(id__in=attr).get_descendants().values_list('id',flat=True)

        return list(attr)

    def to_representation(self, instance):
        result=super().to_representation(instance)
        result['button']=Mean.objects.filter(id__in=result['button']).values_list('name',flat=True)[:10]
        result['department'] = Department.objects.filter(id__in=result['department']).values_list('name', flat=True)[:10]
        return result

    class Meta:
        model=Roles
        exclude=('is_active',)

class UserRolesSerializer(serializers.ModelSerializer):
    user=serializers.HiddenField(default=serializers.CurrentUserDefault(),label='用户')
    is_roles=serializers.BooleanField(label='是否默认')
    role=serializers.StringRelatedField(label='角色')
    department=serializers.StringRelatedField(label='角色所属部门')

    def validate_is_roles(self, attr):
        UserRoles.objects.filter(user=self.context['request'].user,is_roles=True).update(is_roles=False)
        return attr

    class Meta:
        model=UserRoles
        fields=('id','user','is_roles','role','department')


class CmsUserRolesSerializer(serializers.ModelSerializer):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.context['request'].method=='GET':
            self.fields['user']=serializers.StringRelatedField()
            self.fields['department']=serializers.StringRelatedField()
            self.fields['role']=serializers.StringRelatedField()
        else:
            #只有被角色所属分院包含的才能够看到该角色
            role=Roles.objects.all()
            temp=[]
            for i in role:
                for a in i.department:
                    if a in self.context['request'].dept_ids:
                        temp.append(a)
            print(role)
            self.fields['role'] = serializers.PrimaryKeyRelatedField(required=True,queryset=role,
                                                                   label='角色',write_only=True)
            #只能选择用户角色已有部门权限下的部门
            self.fields['department']=serializers.PrimaryKeyRelatedField(required=True,write_only=True,
                                queryset=Department.objects.filter(id__in=self._context['request'].dept_ids),
                                                                   label='部门')


    class Meta:
        model=UserRoles
        exclude=('is_active','is_roles')