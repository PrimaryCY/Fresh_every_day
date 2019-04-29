from django.db import models
from django.contrib.auth.models import AbstractBaseUser,AbstractUser
from django.db.models import Max,aggregates
from django.contrib.auth.hashers import make_password
from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey
from jsonfield.fields import JSONField

from utils.models import BaseModel



class Department(MPTTModel):
    """部门"""

    parent=TreeForeignKey('self',on_delete=models.CASCADE,related_name='child',
                                verbose_name='父亲ID',null=True,blank=True)
    name=models.CharField(max_length=100,verbose_name='部门名称')
    desc = models.TextField(max_length=100, verbose_name='部门描述')
    is_active=models.BooleanField(default=True,verbose_name='是否激活')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    has_child=JSONField(default=[],verbose_name='子级菜单')


    class Meta:
        verbose_name_plural = verbose_name = '菜单'

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name




class Mean(MPTTModel):
    """菜单"""
    parent = TreeForeignKey('self', on_delete=models.CASCADE, related_name='child',
                                  verbose_name='父菜单', null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name='按钮名称')
    desc = models.TextField(max_length=100, verbose_name='按钮描述')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    class Meta:
        verbose_name_plural = verbose_name = '菜单权限'

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class Roles(BaseModel):
    """角色"""
    name=models.CharField(max_length=50,verbose_name='角色名称')
    desc=models.TextField(default='暂无',null=True,blank=True,verbose_name='角色描述')
    button=models.ManyToManyField(Mean,verbose_name='按钮')
    created_user=models.ForeignKey('User',on_delete=models.CASCADE,null=True,blank=True,
                                   verbose_name='创建人')
    department=JSONField(default=[],verbose_name='角色所处部门')

    class Meta:
        verbose_name_plural = verbose_name = '角色'

    def __str__(self):
        return self.name


class UserRoles(BaseModel):
    user=models.ForeignKey('User',on_delete=models.CASCADE,verbose_name='用户')
    role=models.ForeignKey('Roles',on_delete=models.CASCADE,verbose_name='角色')
    department=models.ForeignKey('Department',on_delete=models.CASCADE,verbose_name='角色所属部门权限')
    is_roles=models.BooleanField(default=False,verbose_name='是否默认使用')


    def __str__(self):
        return f'{self.user}:{self.role}'

    class Meta:
        verbose_name_plural = verbose_name = '用户表'




class User(BaseModel,AbstractBaseUser):
    admin_choices=(
        (0,'普通用户'),
        (1,'管理员账户')
    )
    gender_choices=(
        (0,'女'),
        (1,'男'),
        (2,'保密')
    )
    username=models.CharField(max_length=50,unique=True,verbose_name='用户名')
    phone=models.CharField(unique=True,max_length=11,verbose_name='手机号码')
    is_admin=models.SmallIntegerField(default=0,choices=admin_choices,verbose_name='后台用户')
    email = models.EmailField(max_length=100,null=True,blank=True,verbose_name='邮箱')
    is_email=models.BooleanField(default=False,verbose_name='邮箱认证')
    gender=models.SmallIntegerField(choices=gender_choices,default=2,verbose_name='性别')
    portrait=models.ImageField(null=True,blank=True,verbose_name='头像')
    is_phone=models.BooleanField(default=False,verbose_name='手机认证')
    age=models.SmallIntegerField(null=True,blank=True,verbose_name='年龄')
    department=models.ForeignKey(Department,on_delete=models.CASCADE,null=True,verbose_name='所在部门')
    user_post=models.CharField(max_length=50,verbose_name='用户职位')

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name_plural=verbose_name='用户表'

    def __str__(self):
        return self.username if self.username else self.phone

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_password(self.password)
        super().save(force_insert, force_update, using, update_fields)


class UserAddress(BaseModel):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True,verbose_name='用户')
    province = models.CharField(max_length=100, verbose_name="省份")
    city = models.CharField(max_length=100, verbose_name="城市")
    district = models.CharField(max_length=100, verbose_name="区域")
    address = models.CharField(max_length=100, verbose_name="详细地址")
    signer_name = models.CharField(max_length=100,  verbose_name="签收人")
    signer_mobile = models.CharField(max_length=11,  verbose_name="电话")
    default_addr=models.BooleanField(default=False,verbose_name='是否默认')
    zip_code=models.CharField(max_length=10,null=True,blank=True,verbose_name="邮政编码")


    class Meta:
        verbose_name_plural=verbose_name='收货地址'

    def __str__(self):
        return self.address



class Group(BaseModel):
    """分组"""
    user=models.ForeignKey(User,on_delete=models.CASCADE,verbose_name='用户')
    role=models.ForeignKey(Roles,on_delete=models.CASCADE,verbose_name='角色')



class Tree(MPTTModel):
    name = models.CharField('名称', max_length=100, unique=True)
    desc = models.TextField('网站简介', blank=True)
    link = models.URLField('网站地址', blank=True)
    c_time = models.DateTimeField(auto_now_add=True)

    parent = TreeForeignKey('self',on_delete=models.CASCADE,verbose_name='上一级', null=True,
                            blank=True, related_name='children')



    class Meta:
        verbose_name = verbose_name_plural = '国家/组织'

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name