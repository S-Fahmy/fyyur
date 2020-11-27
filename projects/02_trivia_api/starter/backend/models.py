import os
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_migrate import Migrate

import json


db = SQLAlchemy()


def setup_db(app):

    db.app = app
    db.init_app(app)
    Migrate(app, db)


def setup_test_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://{}:{}@{}/{}".format(
        'postgres', 'root', 'localhost: 5432', 'trivia_test')
    db.app = app
    db.init_app(app)


'''
Question

'''


class Question(db.Model):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    question = Column(String,  nullable=False)
    answer = Column(String,  nullable=False)
    # category = Column(String) ?????
    difficulty = Column(Integer,  nullable=False)

    # for now, each question belongs to only one categore not many. so i'm creating manytomany relationship
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    def __init__(self, question, answer, difficulty, category_id):
        self.question = question
        self.answer = answer
        # self.category = category
        self.difficulty = difficulty
        self.category_id = category_id

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category_id, #the front end expects a category value containing the category id.
            'difficulty': self.difficulty,
            # 'category_id': self.category_id
        }


'''
Category

'''


class Category(db.Model):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    type = Column(String,  nullable=False)

    # myTODO: think if it should be lazy loaded or eager loaded.
    questions = relationship(
        "Question", backref="category", lazy=True, cascade="all, delete-orphan")

    def __init__(self, type):
        self.type = type

    def format(self):
        return {
            'id': self.id,
            'type': self.type
        }
