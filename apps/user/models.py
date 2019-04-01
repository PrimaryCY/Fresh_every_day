from django.db import models
from django.contrib.auth.models import AbstractBaseUser,AbstractUser

from utils.models import BaseModel


class User(AbstractBaseUser,BaseModel):
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

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name_plural=verbose_name='用户表'

    def __str__(self):
        return self.username if self.username else self.phone

class UserAddress(BaseModel):
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,verbose_name='用户')
    province = models.CharField(max_length=100, default="", verbose_name="省份")
    city = models.CharField(max_length=100, default="", verbose_name="城市")
    district = models.CharField(max_length=100, default="", verbose_name="区域")
    address = models.CharField(max_length=100, default="", verbose_name="详细地址")
    signer_name = models.CharField(max_length=100, default="", verbose_name="签收人")
    signer_mobile = models.CharField(max_length=11, default="", verbose_name="电话")
    default_addr=models.BooleanField(default=False,verbose_name='是否默认')

    class Meta:
        verbose_name_plural=verbose_name='收货地址'

    def __str__(self):
        return self.address
