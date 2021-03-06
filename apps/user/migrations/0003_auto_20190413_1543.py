# Generated by Django 2.1.7 on 2019-04-13 15:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20190413_1127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roles',
            name='created_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='创建人'),
        ),
        migrations.AlterField(
            model_name='roles',
            name='desc',
            field=models.TextField(blank=True, default='暂无', null=True, verbose_name='角色描述'),
        ),
    ]
