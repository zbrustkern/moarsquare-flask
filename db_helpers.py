import os
import psycopg2

def get_db_connection():
    if 'ON_HEROKU' in os.environ:
        connection = psycopg2.connect(
            os.getenv('DATABASE_URL'), 
            sslmode='require'
        )
    else:
        connection = psycopg2.connect(
            host='localhost',
            database=os.getenv('POSTGRES_DATABASE'),
        )
    return connection

def consolidate_comments_in_posts(posts_with_comments):
    print(posts_with_comments)
    consolidated_posts = []
    for post in posts_with_comments:
        post_exists = False
        for consolidated_post in consolidated_posts:
            if post["id"] == consolidated_post["id"]:
                post_exists = True
                consolidated_post["comments"].append(
                    {"comment_text": post["comment_text"],
                     "comment_id": post["comment_id"],
                     "comment_author_username": post["comment_author_username"]
                    })
                break

        if not post_exists:
            post["comments"] = []
            if post["comment_id"] is not None:
                post["comments"].append(
                    {"comment_text": post["comment_text"],
                     "comment_id": post["comment_id"],
                     "comment_author_username": post["comment_author_username"]
                    }
                )
            del post["comment_id"]
            del post["comment_text"]
            del post["comment_author_username"]
            consolidated_posts.append(post)

    return consolidated_posts