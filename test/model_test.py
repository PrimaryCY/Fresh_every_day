# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/11 21:35

from apps.user.models import Department

obj=Department._default_manager
from test.sql import MyPysql
a=MyPysql()
b=a.DQLall(f"select id,title,parent_id,level from user_dept where is_active=1 order  by parent_id,id")
from datetime import datetime
# for i in b:
#     print(i)
#     if i[2]==0:
#         parent_obj=None
#     else:
#         parent_obj=Department.objects.get(id=i[2])
#     obj.create(id=i[0],name=i[1],parent=parent_obj)
#     # obj.id=i[0]
    # obj.name=i[1]
    # if i[2]!=0:
    #     obj.parent_id=i[2]
    # obj.created_time=datetime.now()
    #obj.level=i[3]
    #obj.save()








