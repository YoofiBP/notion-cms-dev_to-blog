import psycopg2

connection = psycopg2.connect(
    host="localhost",
    database="notion_cms",
    user="yoofi"
)

cur = connection.cursor()
cur.execute("SELECT version()")
db_version = cur.fetchone()
print(db_version)

cur.close()
