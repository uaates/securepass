import sys, os, json, random, string, math
from datetime import datetime
from cryptography.fernet import Fernet
import pyperclip

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QSlider, QCheckBox,
    QMessageBox, QProgressBar, QTableView
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont

# ==========================================================
# CONFIG
# ==========================================================
DATA_JSON = "passwords.json"
KEY_FILE = "secret.key"

PLATFORMS = [
    "Instagram", "Twitter", "Steam", "Spotify",
    "Gmail", "Discord", "Reddit", "Twitch", "Diğer"
]

os.makedirs("backups", exist_ok=True)

# ==========================================================
# SECURITY
# ==========================================================
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as f:
        f.write(Fernet.generate_key())

fernet = Fernet(open(KEY_FILE, "rb").read())

def encrypt_pw(pw: str):
    return fernet.encrypt(pw.encode()).decode()

def decrypt_pw(enc: str):
    try:
        return fernet.decrypt(enc.encode()).decode()
    except:
        return "Çözülemedi"

# ==========================================================
# DATA
# ==========================================================
def load_records():
    if not os.path.exists(DATA_JSON):
        return []
    try:
        return json.load(open(DATA_JSON, encoding="utf-8"))
    except:
        return []

def save_all(records):
    json.dump(records, open(DATA_JSON, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

# ==========================================================
# PASSWORD
# ==========================================================
def generate_password(length=12, symbols=True):
    chars = string.ascii_letters + string.digits
    if symbols:
        chars += "!@#$%^&*()-_=+"
    while True:
        pw = ''.join(random.choice(chars) for _ in range(length))
        if any(c.islower() for c in pw) and any(c.isupper() for c in pw) and any(c.isdigit() for c in pw):
            return pw

def strength_bits(pw):
    return math.log2(len(set(pw)) ** len(pw))

def strength_info(bits):
    if bits < 35: return "Zayıf", 30
    if bits < 60: return "Orta", 65
    return "Güçlü", 100

# ==========================================================
# TABLE MODEL
# ==========================================================
class PasswordTableModel(QAbstractTableModel):
    HEADERS = ["Platform", "Kullanıcı", "Oluşturma"]

    def __init__(self, records, owner):
        super().__init__()
        self.owner = owner
        self.records = [r for r in records if r["owner"] == owner]

    def rowCount(self, parent=None):
        return len(self.records)

    def columnCount(self, parent=None):
        return 3

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        r = self.records[index.row()]
        return [r["platform"], r["username"], r["created_at"][:19]][index.column()]

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]

    def refresh(self):
        self.beginResetModel()
        all_data = load_records()
        self.records = [r for r in all_data if r["owner"] == self.owner]
        self.endResetModel()

# ==========================================================
# MAIN UI
# ==========================================================
class SecurePass(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SecurePass")
        self.setFixedSize(980, 560)
        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)

        title = QLabel("🔐 SecurePass")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        root.addWidget(title)

        self.owner = QLineEdit()
        self.owner.setPlaceholderText("Kendi kullanıcı adını gir")
        root.addWidget(self.owner)

        body = QHBoxLayout()
        root.addLayout(body)

        # LEFT
        left = QVBoxLayout()
        body.addLayout(left, 1)

        self.platform = QComboBox()
        self.platform.addItems(PLATFORMS)

        self.username = QLineEdit()
        self.length = QSlider(Qt.Horizontal)
        self.length.setRange(8, 64)
        self.length.setValue(12)
        self.symbols = QCheckBox("Semboller")

        left.addWidget(QLabel("Platform"))
        left.addWidget(self.platform)
        left.addWidget(QLabel("Kullanıcı"))
        left.addWidget(self.username)
        left.addWidget(QLabel("Uzunluk"))
        left.addWidget(self.length)
        left.addWidget(self.symbols)

        # RIGHT
        right = QVBoxLayout()
        body.addLayout(right, 1)

        self.password = QLineEdit()
        self.password.setAlignment(Qt.AlignCenter)
        self.password.setFont(QFont("Consolas", 15))
        self.password.setReadOnly(True)

        self.progress = QProgressBar()
        self.strength = QLabel("Güç: -")

        right.addWidget(self.password)
        right.addWidget(self.progress)
        right.addWidget(self.strength)

        btn_gen = QPushButton("Oluştur")
        btn_gen.clicked.connect(self.generate)
        btn_save = QPushButton("Kaydet")
        btn_save.clicked.connect(self.save)

        right.addWidget(btn_gen)
        right.addWidget(btn_save)

        # TABLE
        self.table = QTableView()
        root.addWidget(QLabel("📊 Kayıtlarım"))
        root.addWidget(self.table)

        # ACTIONS
        act = QHBoxLayout()
        root.addLayout(act)

        btn_edit = QPushButton("✏️ Düzenle")
        btn_delete = QPushButton("🗑 Sil")

        btn_edit.clicked.connect(self.edit)
        btn_delete.clicked.connect(self.delete)

        act.addWidget(btn_edit)
        act.addWidget(btn_delete)

        self.setStyleSheet("""
            QWidget { background:#121212; color:#eee; }
            QLineEdit, QComboBox { background:#1e1e1e; padding:6px; border-radius:6px; }
            QPushButton { background:#2979ff; padding:8px; border-radius:6px; }
            QPushButton:hover { background:#5393ff; }
        """)

    # ===== LOGIC =====
    def generate(self):
        pw = generate_password(self.length.value(), self.symbols.isChecked())
        self.password.setText(pw)
        bits = strength_bits(pw)
        label, val = strength_info(bits)
        self.progress.setValue(val)
        self.strength.setText(f"Güç: {label}")

    def save(self):
        if not self.owner.text():
            QMessageBox.warning(self, "Uyarı", "Kullanıcı adı gir")
            return

        data = load_records()
        data.append({
            "owner": self.owner.text(),
            "platform": self.platform.currentText(),
            "username": self.username.text(),
            "password_enc": encrypt_pw(self.password.text()),
            "created_at": datetime.now().isoformat()
        })
        save_all(data)
        self.refresh_table()

    def refresh_table(self):
        self.model = PasswordTableModel(load_records(), self.owner.text())
        self.table.setModel(self.model)

    def edit(self):
        idx = self.table.currentIndex().row()
        if idx < 0:
            return
        rec = self.model.records[idx]
        self.username.setText(rec["username"])
        self.platform.setCurrentText(rec["platform"])

    def delete(self):
        idx = self.table.currentIndex().row()
        if idx < 0:
            return

        if QMessageBox.question(self, "Sil", "Bu kayıt silinsin mi?") != QMessageBox.Yes:
            return

        all_data = load_records()
        rec = self.model.records[idx]
        all_data.remove(rec)
        save_all(all_data)
        self.refresh_table()

# ==========================================================
# START
# ==========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SecurePass()
    win.show()
    sys.exit(app.exec())
