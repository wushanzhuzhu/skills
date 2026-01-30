import pymysql
from dbutils.pooled_db import PooledDB
from contextlib import contextmanager

class MySQLClient:
    def __init__(self, host, user, password, database=None, **kwargs):
        """
        :param database: 可选，连接时指定默认database
        :param kwargs: 其他pymysql参数（如port, charset等）
        """
        self.pool_config = {
            'host': host,
            'user': user,
            'password': password,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            **kwargs
        }
        
        # 如果初始化时指定了database，则创建专用连接池
        if database:
            self.pool_config['database'] = database
            self.pool = PooledDB(
                creator=pymysql,
                mincached=2,
                maxcached=5,
                **self.pool_config
            )
        else:
            # 未指定database时创建通用连接池（需手动指定database）
            self.pool = PooledDB(
                creator=pymysql,
                mincached=2,
                maxcached=5,
                **{k: v for k, v in self.pool_config.items() if k != 'database'}
            )
    
    @contextmanager
    def _conn_context(self, database=None):
        """获取带database的连接"""
        conn = self.pool.connection()
        original_db = None
        
        if database:
            # 保存当前数据库
            with conn.cursor() as cursor:
                cursor.execute("SELECT DATABASE()")
                original_db = cursor.fetchone()['DATABASE()']
            
            # 切换到目标数据库
            with conn.cursor() as cursor:
                cursor.execute(f"USE `{database}`")
        
        try:
            yield conn
        finally:
            # 如果切换了数据库，尝试切回原来的数据库
            if original_db and original_db != database:
                with conn.cursor() as cursor:
                    cursor.execute(f"USE `{original_db}`")
            conn.close()
    
    def execute(self, sql, params=None, database=None):
        """通用执行方法"""
        with self._conn_context(database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                conn.commit()
                return cursor.fetchall() if cursor.description else None
    
    def add(self, table, database=None, **kwargs):
        """插入数据"""
        keys = ', '.join([f"`{k}`" for k in kwargs.keys()])
        values = ', '.join(['%s'] * len(kwargs))
        sql = f"INSERT INTO `{table}` ({keys}) VALUES ({values})"
        return self.execute(sql, list(kwargs.values()), database)
    
    def delete(self, table, condition, database=None):
        """删除数据"""
        sql = f"DELETE FROM `{table}` WHERE {condition}"
        return self.execute(sql, database=database)
    
    def update(self, table, set_values, condition, database=None):
        """更新数据"""
        set_clause = ', '.join([f"`{k}`=%s" for k in set_values])
        sql = f"UPDATE `{table}` SET {set_clause} WHERE {condition}"
        return self.execute(sql, list(set_values.values()), database)
    
    def query(self, table, fields="*", condition="", database=None):
        """查询数据
        Args:
            table: 数据库表名，必填
            fields: select后面的查询字段（默认"*"），支持任意表达式如"COUNT(*)"、"name,id"等
            condition: WHERE子条件（可选）,例如where name='wushan'
            database: 数据库名,必填
        """
        # 动态构建SELECT字段部分
        sql = f"SELECT {fields} FROM `{table}`"
        if condition:
            sql += f" WHERE {condition}"
        print("MySQLClient sql: ", sql)
        return self.execute(sql, database=database)
    
    def query_simple(self, sql, database=None):
        """
        直接使用SELECT语句查询数据
        """
        print("MySQLClient sql: ", sql)
        if not database: 
            return "请指定数据库"
        return self.execute(sql, database=database)

# 使用示例
if __name__ == "__main__":
    # 方案1：创建专用连接池（指定默认database）
    db1 = MySQLClient(
        host='10.192.62.100',
        user='root',
        password='cloudadmin#Passw0rd',
        database='xu_resource',
        port=3306
    )
    #查询示例
    db1.query('virtual_machine',"name='wushan123'")
    
    # 方案2：创建通用连接池（动态指定database）
    db2 = MySQLClient(
        host='10.192.62.100',
        user='root',
        password='cloudadmin#Passw0rd',
        port=3306
    )
    #查询示例
    print(db2.query('virtual_machine',"name='wushan123'",database='xu_resource'))