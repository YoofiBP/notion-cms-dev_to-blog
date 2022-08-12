import psycopg2

connection = psycopg2.connect(
    host="localhost",
    database="notion_cms",
    user="yoofi"
)
