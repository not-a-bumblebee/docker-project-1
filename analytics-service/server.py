from flask import Flask, jsonify
import mysql.connector
from pymongo import MongoClient
import os

app = Flask(__name__)

def get_mysql_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mysql"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "rootpassword"),
        database=os.getenv("DB_NAME", "analytics_db")
    )

def get_mongo_collection():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://mongodb:27017/"))
    return client["analytics_results"]["stats"]

@app.route('/trigger-analytics', methods=['POST'])
def trigger_analytics():
    try:
        # 1. Connect to MySQL and run aggregate query
        db_mysql = get_mysql_db()
        cursor = db_mysql.cursor()
        cursor.execute("""
            SELECT course, MIN(grade) as min_val, MAX(grade) as max_val, 
                   AVG(grade) as avg_val, COUNT(grade) as count_val 
            FROM course_grades GROUP BY course
        """)
        results = cursor.fetchall()
        cursor.close()
        db_mysql.close()
        
        # 2. Write computed aggregate summary directly to MongoDB
        mongo_col = get_mongo_collection()
        for row in results:
            stat_doc = {
                "course": row[0],
                "min_val": row[1],
                "max_val": row[2],
                "avg_val": row[3],
                "count_val": row[4]
            }
            mongo_col.update_one(
                {"course": stat_doc["course"]},
                {"$set": stat_doc},
                upsert=True
            )
            
        return jsonify({"success": True, "message": "Analytics synced to MongoDB successfully."}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)