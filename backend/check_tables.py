import sqlite3

connection = sqlite3.connect("skillswap.db")
rows = connection.execute("select name from sqlite_master where type='table'")
print(sorted(name for (name,) in rows))
