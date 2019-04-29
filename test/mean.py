# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/13 13:38
from test.sql import MyPysql
from apps.user.models import Mean

obj=Mean._default_manager

a=MyPysql()
b=a.DQLall(f"SELECT id,title,parent_id  FROM x_men_menu where is_active=1 order  by parent_id,id")

for i in b:
    print(i)
    if i[2]==0:
        parent_obj=None
    else:
        parent_obj=Mean.objects.get(id=i[2])
    obj.create(id=i[0], name=i[1], parent=parent_obj)
