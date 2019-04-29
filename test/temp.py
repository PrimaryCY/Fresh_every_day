# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/22 18:37
import test
from apps.user.models import Department
from django.db.models import Field

obj=Department.objects
# for i in obj:
#    print(i.id)
print('原始','*'*10)
field_list = ['6','3','4']
temp=','.join(field_list)
filed='id'
field_sql=f"FIELD(`id`,{temp})"
print(field_sql)
cc=obj.extra(select={'field_sql' : field_sql},where=[f'id IN ({temp})'],order_by=['field_sql'])
print(cc)
for i in cc:
    print(i.id)

