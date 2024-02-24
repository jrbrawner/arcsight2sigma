import logging

LOGGER = logging.basicConfig(filename='example.log', encoding='utf-8')

SQLALCHEMY_DATABASE_URI = 'sqlite:///development.db'