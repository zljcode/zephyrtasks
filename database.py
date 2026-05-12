import sqlite3
import os


class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_dir = os.path.join(os.path.expanduser("~"), ".ZephyrTasks")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "tasks.db")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                completed_at TEXT
            )
        """)
        self.conn.commit()

    def add_task(self, title):
        cursor = self.conn.execute(
            "INSERT INTO tasks (title) VALUES (?)", (title,)
        )
        self.conn.commit()
        return cursor.lastrowid

    def toggle_task(self, task_id):
        task = self.conn.execute(
            "SELECT completed FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
        if task is None:
            return
        new_state = 0 if task["completed"] else 1
        completed_at = "datetime('now','localtime')" if new_state else "NULL"
        if new_state:
            self.conn.execute(
                "UPDATE tasks SET completed=?, completed_at=datetime('now','localtime') WHERE id=?",
                (new_state, task_id),
            )
        else:
            self.conn.execute(
                "UPDATE tasks SET completed=?, completed_at=NULL WHERE id=?",
                (new_state, task_id),
            )
        self.conn.commit()

    def delete_task(self, task_id):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def update_task(self, task_id, title):
        """更新任务标题，返回是否更新成功"""
        cursor = self.conn.execute(
            "UPDATE tasks SET title=? WHERE id=?", (title, task_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def clear_completed_tasks(self):
        """删除所有已完成任务，返回删除数量"""
        cursor = self.conn.execute("DELETE FROM tasks WHERE completed=1")
        self.conn.commit()
        return cursor.rowcount

    def get_all_tasks(self):
        cursor = self.conn.execute("""
            SELECT * FROM tasks
            ORDER BY completed ASC,
                     CASE WHEN completed=0 THEN created_at END DESC,
                     CASE WHEN completed=1 THEN completed_at END DESC,
                     id ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()
