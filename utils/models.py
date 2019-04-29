# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 19:00

from django.db import models

class BaseModelMange(models.Manager):

    def all(self):
        return self.filter(is_active=True).all()

    def filter(self,*args,**kwargs):
        if not kwargs.get('is_active'):
            kwargs['is_active'] = True
        return super().filter(*args,**kwargs)


class BaseModel(models.Model):
    """基本model"""
    created_time=models.DateTimeField(auto_now_add=True,verbose_name='创建时间')
    update_time=models.DateTimeField(auto_now=True,verbose_name='修改时间')
    is_active=models.BooleanField(default=True,verbose_name='状态')
    objects=BaseModelMange()
    raw_objects=models.Manager()

    class Meta:
        abstract=True
