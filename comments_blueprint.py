from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
import psycopg2.extras
import datetime
from auth_middleware import token_required

comments_blueprint = Blueprint('comments_blueprint', __name__)

@comments_blueprint.route('/posts/<post_id>/comments', methods=['POST'])
@token_required
def create_comment(post_id):
    try:
        new_comment_data = request.get_json()
        new_comment_data["author"] = g.user["id"]
        current_time = datetime.datetime.now()

        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
                        INSERT INTO comments (post, author, text, created_at)
                        VALUES (%s, %s, %s, %s)
                        RETURNING *
                        """,
                        (post_id, new_comment_data['author'], new_comment_data['text'], current_time)
        )
        created_comment = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify({"comment": created_comment}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@comments_blueprint.route('/posts/<post_id>/comments/<comment_id>', methods=['PUT'])
@token_required
def update_comment(post_id, comment_id):
    try:
        updated_comment_data = request.json
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM comments WHERE id = %s", (comment_id,))
        comment_to_update = cursor.fetchone()
        if comment_to_update is None:
            return jsonify({"error": "Comment not found"}), 404
        if comment_to_update["author"] != g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401
        cursor.execute("UPDATE comments SET text = %s WHERE id = %s RETURNING *",
                       (updated_comment_data["text"], comment_id))
        updated_comment = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify({"comment": updated_comment}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@comments_blueprint.route('/posts/<post_id>/comments/<comment_id>', methods=['DELETE'])
@token_required
def delete_comment(post_id, comment_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM comments WHERE id = %s", (comment_id,))
        comment_to_delete = cursor.fetchone()
        if comment_to_delete is None:
            return jsonify({"error": "Comment not found"}), 404
        if comment_to_delete["author"] != g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401
        cursor.execute("DELETE FROM comments WHERE id = %s", (comment_id,))
        connection.commit()
        connection.close()
        return jsonify({"message": "Comment deleted successfully"}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500