from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
import psycopg2.extras
import datetime
from auth_middleware import token_required

likes_blueprint = Blueprint('likes_blueprint', __name__)

@likes_blueprint.route('/posts/<post_id>/likes', methods=['POST'])
@token_required
def create_like(post_id):
    try:
        new_like_data = request.get_json()
        new_like_data["author"] = g.user["id"]
        current_time = datetime.datetime.now()

        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
                        INSERT INTO likes (post, author, created_at)
                        VALUES (%s, %s, %s)
                        RETURNING *
                        """,
                        (post_id, new_like_data['author'], current_time)
        )
        created_like = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify({"like": created_like}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    
@likes_blueprint.route('/posts/<post_id>/likes/<like_id>', methods=['DELETE'])
@token_required
def delete_like(post_id, like_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM likes WHERE id = %s", (like_id,))
        like_to_delete = cursor.fetchone()
        if like_to_delete is None:
            return jsonify({"error": "Like not found"}), 404
        if like_to_delete["author"] != g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401
        cursor.execute("DELETE FROM likes WHERE id = %s", (like_id,))
        connection.commit()
        connection.close()
        return jsonify({"message": "Like deleted successfully"}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500