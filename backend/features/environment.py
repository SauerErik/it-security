import sys
import os
from flask import Flask

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, os.pardir, os.pardir)
project_root_dir = os.path.join(backend_dir, os.pardir)

if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

try:
    from backend.models import db
except ImportError as e:
    print(f"FATAL ERROR: Failed to import backend.models. DB setup will fail. Error: {e}")


# ----------------------------------------------------------------------
# HOOKS
# ----------------------------------------------------------------------

def before_all(context):

    context.app = Flask('test-studyconnect')
    context.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    context.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    context.app.config['TESTING'] = True
    db.init_app(context.app)

    context.user = None
    context.group = None
    context.task = None
    context.exception = None


def before_scenario(context, scenario):
    context.app_context = context.app.app_context()
    context.app_context.push()
    db.create_all()


def after_scenario(context, scenario):
    db.session.remove()
    db.drop_all()
    context.app_context.pop()
