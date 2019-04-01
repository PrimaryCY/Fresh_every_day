# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/31 0:39
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

User=get_user_model()

@receiver(post_save,sender=User)
def create_user(sender, instance = None, created = False, ** kwargs):
    if created:
        instance.set_password(instance.password)
        instance.save()