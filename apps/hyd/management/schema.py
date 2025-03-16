import sqlalchemy
from sqlalchemy import orm

Base = orm.declarative_base()


class TaskProgress(Base):
    __tablename__ = 'progress'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    # Name of the task
    label = sqlalchemy.Column(sqlalchemy.String)
    # Current progress value
    value = sqlalchemy.Column(sqlalchemy.Integer)
    # Maximum progress value
    max_value = sqlalchemy.Column(sqlalchemy.Integer)
    # Current status of the task
    status = sqlalchemy.Column(sqlalchemy.String, nullable=True)
