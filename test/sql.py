# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/12 13:02
import pymysql,yaml,os,logging
from datetime import date, timedelta, time
from sshtunnel import SSHTunnelForwarder

#获取配置文件路径
#config_path=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
#mysql_con=os.path.join('web','config','MySQL.yml')


class MyPysql(object):



    def __init__(self):
        #远程ssh链接
        self.sqlserver = SSHTunnelForwarder(
            ssh_address_or_host=('192.168.9.133', 22),  # 指定ssh登录的跳转机的address
            ssh_username='ubuntu',  # 跳转机的用户
            ssh_password='ubuntu',  # 跳转机的密码
            remote_bind_address=('172.16.0.4', 3306))
        self.sqlserver.start()

        # 配置文件
        base_dir=os.path.dirname(__file__)
        mysql_con = os.path.join(base_dir, 'MySQL.yml')

        f = open(mysql_con, encoding='utf-8')
        self.config = yaml.load(f)
        f.close()

        self.connect=None
        self.cursor=None

    #只返回一行dql语句返回值
    def DQLone(self,sql,*args):
        try:
            self.connect=pymysql.connect(port=self.sqlserver,currsorclass=pymysql.
                                         cursors.DictCursor,**self.config)
            self.cursor=self.connect.cursor()
            self.cursor.execute(sql,args)
            return self.cursor.fetchone()
        except Exception as ex:
            print(str(ex))
        finally:
            self.close()


    #关闭游标和连接
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connect:
            self.connect.close()
        self.sqlserver.stop()

    #返回dql语句执行后所有的返回值
    def DQLall(self,sql,*args):
        try:
            self.connect = pymysql.connect(port=self.sqlserver.local_bind_port,
                                        **self.config)

            self.cursor=self.connect.cursor()
            self.cursor.execute(sql,args)
            return self.cursor.fetchall()
        except Exception as ex:
            logging.error(str(ex))
        finally:
            self.close()

    #返回任意个dql语句返回值
    def DQLmany(self,sql,*args,num=1):
        try:
            self.connect = pymysql.connect(port=self.sqlserver.local_bind_port,
                                           **self.config)

            self.cursor=self.connect.cursor()
            self.cursor.execute(sql,args)
            return self.cursor.fetchmany(num)
        except Exception as ex:
            logging.error(str(ex))
        finally:
            self.close()

    #执行dml语句，并返回受影响的行数
    def DML(self,sql,*args):
        try:
            self.connect = pymysql.connect(port=self.sqlserver.local_bind_port,
                                           **self.config)
            self.cursor=self.connect.cursor()
            row=self.cursor.execute(sql,args)
            #没有异常就确认事务
            self.connect.commit()
            return row
        except Exception as ex:
            #捕获到异常就rollback
            self.connect.rollback()
            logging.error(str(ex))
        #不管异常结果怎么样，都关闭链接
        finally:
            self.close()


if __name__ == "__main__":
    a=MyPysql()
    b=a.DQLall(f"select title,parent_id from user_dept where is_active=1")
    #a.close()
    print(b)
    print(type(b))
