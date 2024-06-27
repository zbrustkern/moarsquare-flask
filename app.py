from flask import Flask, jsonify, request, g
from flask_cors import CORS
from dotenv import load_dotenv
from auth_blueprint import authentication_blueprint
from auth_middleware import token_required
from posts_blueprint import posts_blueprint
from comments_blueprint import comments_blueprint
from likes_blueprint import likes_blueprint
import os
import jwt
import psycopg2, psycopg2.extras
import bcrypt

load_dotenv()

app = Flask(__name__)
CORS(app)
app.register_blueprint(authentication_blueprint)
app.register_blueprint(posts_blueprint)
app.register_blueprint(comments_blueprint)
app.register_blueprint(likes_blueprint)


if __name__ == '__main__':
    app.run()