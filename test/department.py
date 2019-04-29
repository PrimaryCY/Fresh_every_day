# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/12 23:38
import test
from apps.user.models import Department
from itertools import islice
from collections import defaultdict
from multiprocessing import Pool,Manager

def fab(max):
    n, a, b = 0, 0, 1
    while n < max:
        yield b
        # print b
        a, b = b, a + b
        n = n + 1

dic={}
def xx():
    for i,v in zip(Department.objects.all().values('id', 'name','parent_id').iterator(),):
        i.setdefault('child', [])
        i['stop']=i
        dic[i['id']] = i
        yield dic
import time
print(xx())
print(dic)

res=[]
# for k,v in xx():
#     print(xx())
#     if v.get('parent_id'):
#         dic[v['parent_id']]['child'].append(v)
#     else:
#         res.append(v)

print(res)


