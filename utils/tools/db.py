from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


class DatabaseQuery:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        # 从Flask配置获取数据库URI
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///mydb.db')
        app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
        self.db = SQLAlchemy(app)

    def get_table(self, table_name):
        """动态获取数据表模型"""
        return self.db.Model.metadata.tables.get(table_name)

    def execute_query(self, query, parameters=None):
        """执行原始SQL查询"""
        try:
            result = self.db.session.execute(text(query), parameters or {})
            # 处理查询结果
            if result.returns_rows:
                return [dict(row) for row in result.mappings()]
            else:
                self.db.session.commit()
                return {"status": "success", "message": "Query executed"}
        except Exception as e:
            self.db.session.rollback()
            return {"error": str(e)}

    def query_builder(self, table, columns=None, filters=None):
        """构建安全的查询条件"""
        query = self.db.session.query(table)
        if columns:
            query = query.with_entities(*columns)
        if filters:
            query = query.filter(*filters)
        return query.all()


# Flask应用集成示例
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/db'
db_query = DatabaseQuery(app)


# 使用示例
@app.route('/users')
def get_users():
    users = db_query.query_builder(
        table=User,
        columns=[User.id, User.username],
        filters=[User.is_active == True]
    )
    return {"users": [user.to_dict() for user in users]}