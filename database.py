import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name="database.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance REAL DEFAULT 0.0 CHECK (balance >= 0),
                turnover REAL DEFAULT 0.0,
                reg_date TEXT,
                deposits REAL DEFAULT 0.0,
                withdrawals REAL DEFAULT 0.0,
                bonus_spins INTEGER DEFAULT 0 CHECK (bonus_spins >= 0),
                last_bonus_date TEXT,
                referrer_id INTEGER,
                ref_balance REAL DEFAULT 0.0 CHECK (ref_balance >= 0),
                play_mode TEXT DEFAULT 'bot'
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_invoices (
                invoice_id INTEGER PRIMARY KEY
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS turnover_history (
                user_id INTEGER,
                amount REAL,
                date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        # Добавляем колонки если их нет (для существующих БД)
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN bonus_spins INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN last_bonus_date TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN ref_balance REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN play_mode TEXT DEFAULT 'bot'")
        except sqlite3.OperationalError:
            pass
        self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def add_user(self, user_id, username, full_name, referrer_id=None):
        if not self.get_user(user_id):
            reg_date = datetime.now().strftime("%d.%m.%Y")
            self.cursor.execute(
                "INSERT INTO users (user_id, username, full_name, reg_date, referrer_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, full_name, reg_date, referrer_id)
            )
            self.conn.commit()
            return True
        return False

    def get_referrals_count(self, user_id):
        self.cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
        return self.cursor.fetchone()[0]

    def get_referrals_list(self, user_id):
        self.cursor.execute("SELECT full_name FROM users WHERE referrer_id = ?", (user_id,))
        return self.cursor.fetchall()

    def get_top_players(self, period="all_time", limit=10):
        if period == "all_time":
            self.cursor.execute(
                "SELECT full_name, turnover FROM users ORDER BY turnover DESC LIMIT ?", 
                (limit,)
            )
        else:
            # Определение даты в зависимости от периода
            now = datetime.now()
            if period == "today":
                date_str = now.strftime("%Y-%m-%d")
                query = "SELECT u.full_name, SUM(th.amount) as t FROM users u JOIN turnover_history th ON u.user_id = th.user_id WHERE th.date = ? GROUP BY u.user_id ORDER BY t DESC LIMIT ?"
                params = (date_str, limit)
            elif period == "yesterday":
                date_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
                query = "SELECT u.full_name, SUM(th.amount) as t FROM users u JOIN turnover_history th ON u.user_id = th.user_id WHERE th.date = ? GROUP BY u.user_id ORDER BY t DESC LIMIT ?"
                params = (date_str, limit)
            elif period == "week":
                date_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
                query = "SELECT u.full_name, SUM(th.amount) as t FROM users u JOIN turnover_history th ON u.user_id = th.user_id WHERE th.date >= ? GROUP BY u.user_id ORDER BY t DESC LIMIT ?"
                params = (date_start, limit)
            elif period == "month":
                date_start = (now - timedelta(days=30)).strftime("%Y-%m-%d")
                query = "SELECT u.full_name, SUM(th.amount) as t FROM users u JOIN turnover_history th ON u.user_id = th.user_id WHERE th.date >= ? GROUP BY u.user_id ORDER BY t DESC LIMIT ?"
                params = (date_start, limit)
            else:
                return self.get_top_players("all_time", limit)
            
            self.cursor.execute(query, params)
            
        return self.cursor.fetchall()

    def update_turnover(self, user_id, amount):
        self.cursor.execute("UPDATE users SET turnover = turnover + ? WHERE user_id = ?", (amount, user_id))
        # Записываем в историю для топов
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("INSERT INTO turnover_history (user_id, amount, date) VALUES (?, ?, ?)", (user_id, amount, date_str))
        self.conn.commit()

    def update_balance(self, user_id, amount):
        """
        Обновляет баланс пользователя. 
        Для списания передавать отрицательное число.
        Возвращает True если баланс успешно обновлен, False если недостаточно средств.
        """
        if amount < 0:
            self.cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ? AND balance >= ?", 
                (amount, user_id, abs(amount))
            )
            if self.cursor.rowcount == 0:
                return False
        else:
            self.cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        
        self.conn.commit()
        return True

    def update_ref_balance(self, user_id, amount):
        if amount < 0:
            self.cursor.execute(
                "UPDATE users SET ref_balance = ref_balance + ? WHERE user_id = ? AND ref_balance >= ?", 
                (amount, user_id, abs(amount))
            )
            if self.cursor.rowcount == 0:
                return False
        else:
            self.cursor.execute("UPDATE users SET ref_balance = ref_balance + ? WHERE user_id = ?", (amount, user_id))
        
        self.conn.commit()
        return True

    def update_bonus_spins(self, user_id, amount):
        if amount < 0:
            self.cursor.execute(
                "UPDATE users SET bonus_spins = bonus_spins + ? WHERE user_id = ? AND bonus_spins >= ?", 
                (amount, user_id, abs(amount))
            )
            if self.cursor.rowcount == 0:
                return False
        else:
            self.cursor.execute("UPDATE users SET bonus_spins = bonus_spins + ? WHERE user_id = ?", (amount, user_id))
        
        self.conn.commit()
        return True

    def update_last_bonus_date(self, user_id, date_str):
        self.cursor.execute("UPDATE users SET last_bonus_date = ? WHERE user_id = ?", (date_str, user_id))
        self.conn.commit()

    def is_invoice_processed(self, invoice_id):
        self.cursor.execute("SELECT 1 FROM processed_invoices WHERE invoice_id = ?", (invoice_id,))
        return self.cursor.fetchone() is not None

    def mark_invoice_processed(self, invoice_id):
        self.cursor.execute("INSERT OR IGNORE INTO processed_invoices (invoice_id) VALUES (?)", (invoice_id,))
        self.conn.commit()

    def update_deposits(self, user_id, amount):
        self.cursor.execute("UPDATE users SET deposits = deposits + ? WHERE user_id = ?", (amount, user_id))
        self.conn.commit()

    def update_withdrawals(self, user_id, amount):
        self.cursor.execute("UPDATE users SET withdrawals = withdrawals + ? WHERE user_id = ?", (amount, user_id))
        self.conn.commit()

    def update_play_mode(self, user_id, play_mode):
        self.cursor.execute("UPDATE users SET play_mode = ? WHERE user_id = ?", (play_mode, user_id))
        self.conn.commit()

db = Database()
