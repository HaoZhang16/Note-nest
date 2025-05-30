# routes/__init__.py

from flask import Blueprint

# 导入每个蓝图模块
from .auth import auth_bp
from .book import book_bp
from .note import note_bp

# 如果你希望外部统一导入，可以定义一个列表
all_blueprints = [auth_bp, book_bp, note_bp]
