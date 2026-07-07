import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

DB_NAME = "evenodd.db"

connection = sqlite3.connect(DB_NAME)
cursor = connection.cursor()

cursor.execute("DELETE FROM signals WHERE id = ?", ("TEST123",))

connection.commit()
connection.close()

print("Тестовый сигнал TEST123 удалён.")