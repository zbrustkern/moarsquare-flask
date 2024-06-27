from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection, consolidate_comments_in_posts
import psycopg2, psycopg2.extras
from auth_middleware import token_required
import datetime

posts_blueprint = Blueprint('posts_blueprint', __name__)

@posts_blueprint.route('/posts', methods=['GET'])
def posts_index():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""SELECT p.id, p.author AS post_author_id, p.location, p.text, p.created_at, u_post.username AS author_username, c.id AS comment_id, c.text AS comment_text, u_comment.username AS comment_author_username
                            FROM posts p
                            INNER JOIN users u_post ON p.author = u_post.id
                            LEFT JOIN comments c ON p.id = c.post
                            LEFT JOIN users u_comment ON c.author = u_comment.id
                            ORDER BY p.created_at DESC;
                       """)
        posts = cursor.fetchall()
        consolidated_posts = consolidate_comments_in_posts(posts)
        connection.commit()
        connection.close()
        return jsonify({"posts": consolidated_posts}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@posts_blueprint.route('/posts', methods=['POST'])
@token_required
def create_post():
    try:
        new_post = request.json
        new_post["author"] = g.user["id"]
        current_time = datetime.datetime.now()
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
                        INSERT INTO posts (author, location, text, created_at)
                        VALUES (%s, %s, %s, %s)
                        RETURNING *
                        """,
                        (new_post['author'], new_post['location'], new_post['text'], current_time)
        )
        created_post = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify({"post": created_post}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@posts_blueprint.route('/posts/<post_id>', methods=['GET'])
def show_post(post_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT p.id, p.author AS post_author_id, p.location, p.text, u_post.username AS author_username, c.id AS comment_id, c.text AS comment_text, u_comment.username AS comment_author_username
            FROM posts p
            INNER JOIN users u_post ON p.author = u_post.id
            LEFT JOIN comments c ON p.id = c.post
            LEFT JOIN users u_comment ON c.author = u_comment.id
            WHERE p.id = %s;""",
            (post_id,))
        unprocessed_post = cursor.fetchall()
        if unprocessed_post is not None :
            processed_post = consolidate_comments_in_posts(unprocessed_post)[0]
            connection.close()
            return jsonify({"post": processed_post}), 200
        else:
            connection.close()
            return jsonify({"error": "post not found"}), 404
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    
@posts_blueprint.route('/posts/<post_id>', methods=['PUT'])
@token_required
def update_post(post_id):
    try:
        updated_post_data = request.json
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM posts WHERE posts.id = %s", (post_id,))
        post_to_update = cursor.fetchone()
        if post_to_update is None:
            return jsonify({"error": "post not found"}), 404
        connection.commit()
        if post_to_update["author"] is not g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401
        cursor.execute("UPDATE posts SET text = %s, location = %s WHERE posts.id = %s RETURNING *",
                        (updated_post_data["text"], updated_post_data["location"], post_id))
        updated_post = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify({"post": updated_post}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@posts_blueprint.route('/posts/<post_id>', methods=['DELETE'])
@token_required
def delete_post(post_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM posts WHERE posts.id = %s", (post_id,))
        post_to_update = cursor.fetchone()
        if post_to_update is None:
            return jsonify({"error": "post not found"}), 404
        connection.commit()
        if post_to_update["author"] is not g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401
        cursor.execute("DELETE FROM posts WHERE posts.id = %s", (post_id,))
        connection.commit()
        connection.close()
        return jsonify({"message": "post deleted successfully"}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500