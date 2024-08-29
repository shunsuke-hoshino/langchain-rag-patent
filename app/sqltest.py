# sqlite3をインポートする
import sqlite3

# TEST.dbを作成する

dbname = 'TEST.db'
conn = sqlite3.connect(dbname)

cur = conn.cursor()

#テーブルの作成
#cur.execute('''CREATE TABLE users(id real, name text, age text)''')

#データの挿入
cur.execute("INSERT INTO users VALUES (1, 'ヤマダ', '30')")
cur.execute("INSERT INTO users VALUES (2, 'タナカ', '32')")
cur.execute("INSERT INTO users VALUES (3, 'ウエダ', '26')")

#保存（コミット）する
conn.commit()

# tableの中身を確認する
cur.execute('SELECT * FROM users')

# レコード削除
cur.execute("delete from users where id=2")

print(cur.fetchall())

conn.commit()

conn.close()