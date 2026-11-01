"""ThumbYT: arraste uma imagem, digite a palavra, Ctrl+S."""
import os
import sys
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (QImage, QPixmap, QKeySequence, QShortcut, QIcon, QPainter, QColor,
                           QFont, QFontDatabase)
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                               QButtonGroup, QHBoxLayout, QVBoxLayout, QFileDialog, QSizePolicy)
import thumb

STYLE = """
QWidget { background:#0f0f10; color:#e8e8e8; font:14px 'Segoe UI'; }
#view { background:#18181a; border:1px dashed #2c2c30; border-radius:12px; color:#6b6b70; font-size:15px; }
QLineEdit { background:#18181a; border:1px solid #2c2c30; border-radius:8px; padding:10px 12px;
            font-size:16px; font-weight:600; }
QLineEdit:focus { border-color:#f0b20a; }
QPushButton { background:#18181a; border:1px solid #2c2c30; border-radius:8px; padding:10px 16px; }
QPushButton:hover { border-color:#4a4a50; }
QPushButton:checked { border-color:#f0b20a; color:#f0b20a; }
#save { background:#f0b20a; color:#111; font-weight:700; border:none; }
#save:hover { background:#ffc21f; }
"""


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.src = self.img = self.pix = None
        self.setWindowTitle("ThumbYT")
        self.resize(1040, 680)
        self.setAcceptDrops(True)

        self.view = QLabel("Arraste uma imagem aqui\nou clique para abrir", alignment=Qt.AlignCenter,
                           objectName="view", cursor=Qt.PointingHandCursor)
        self.view.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.view.setMinimumSize(320, 180)
        self.view.mousePressEvent = lambda e: self.open()

        self.word = QLineEdit(placeholderText="PALAVRA.")
        self.group = QButtonGroup(self)
        bar = QHBoxLayout(spacing=8)
        bar.addWidget(self.word, 1)
        for label, key in (("Esquerda", "esquerda"), ("Centro", "centro"), ("Direita", "direita")):
            b = QPushButton(label, checkable=True, checked=key == "esquerda")
            b.setProperty("align", key)
            self.group.addButton(b)
            bar.addWidget(b)
        self.scale = 1.0
        self.pct = QLabel("100%", alignment=Qt.AlignCenter, minimumWidth=48)
        bar.addWidget(QPushButton("A−", clicked=lambda: self.zoom(-0.1), toolTip="Diminuir texto (Ctrl+-)"))
        bar.addWidget(self.pct)
        bar.addWidget(QPushButton("A+", clicked=lambda: self.zoom(0.1), toolTip="Aumentar texto (Ctrl+=)"))
        save = QPushButton("Salvar", objectName="save", clicked=self.save)
        bar.addWidget(save)

        lay = QVBoxLayout(self, spacing=12)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.addWidget(self.view, 1)
        lay.addLayout(bar)

        # debounce: re-renderiza 1920x1080 só depois de parar de digitar
        self.timer = QTimer(self, singleShot=True, interval=120, timeout=self.render)
        self.word.textChanged.connect(self.timer.start)
        self.group.buttonClicked.connect(self.timer.start)
        QShortcut(QKeySequence.Save, self, self.save)
        QShortcut(QKeySequence.Open, self, self.open)
        QShortcut(QKeySequence("Ctrl+="), self, lambda: self.zoom(0.1))
        QShortcut(QKeySequence("Ctrl+-"), self, lambda: self.zoom(-0.1))
        self.word.setFocus()

    def zoom(self, step):
        self.scale = round(min(2.0, max(0.3, self.scale + step)), 1)
        self.pct.setText(f"{self.scale:.0%}")
        self.timer.start()

    def open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir imagem", "",
                                              "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)")
        if path:
            self.load(path)

    def load(self, path):
        self.src = path
        self.render()

    def render(self):
        if not self.src:
            return
        try:
            self.img, _ = thumb.render(self.src, self.word.text(), self.group.checkedButton().property("align"),
                                       self.scale)
        except Exception as e:  # arquivo que não é imagem, fonte ausente etc.
            self.src = self.img = self.pix = None
            self.view.setText(f"Erro: {e}")
            return
        self.pix = QPixmap.fromImage(QImage(self.img.tobytes(), thumb.W, thumb.H, 3 * thumb.W,
                                            QImage.Format_RGB888))
        self.fit()

    def fit(self):
        if self.pix:
            self.view.setPixmap(self.pix.scaled(self.view.size(), Qt.KeepAspectRatio,
                                                Qt.SmoothTransformation))

    def save(self):
        if not self.img:
            return
        default = os.path.splitext(self.src)[0] + "_thumb.png"
        path, _ = QFileDialog.getSaveFileName(self, "Salvar thumbnail", default, "PNG (*.png);;JPEG (*.jpg)")
        if path:
            self.img.save(path, quality=95)
            self.setWindowTitle(f"ThumbYT — salvo: {os.path.basename(path)}")

    def resizeEvent(self, e):
        self.fit()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.load(e.mimeData().urls()[0].toLocalFile())


def icon():
    """Quadrado escuro arredondado com 'T.' amarelo, na mesma fonte da thumb."""
    pix = QPixmap(256, 256)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#0f0f10"))
    p.drawRoundedRect(8, 8, 240, 240, 52, 52)
    fams = QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(thumb.FONT or ""))
    font = QFont(fams[0] if fams else "Segoe UI", 150, QFont.Black)
    p.setFont(font)
    p.setPen(QColor(*thumb.YELLOW))
    p.drawText(pix.rect(), Qt.AlignCenter, "T.")
    p.end()
    return QIcon(pix)


if __name__ == "__main__":
    if sys.platform == "win32":  # sem isso a barra de tarefas mostra o ícone do python.exe
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ThumbYT")
    app = QApplication(sys.argv)
    app.setWindowIcon(icon())
    app.setStyleSheet(STYLE)
    w = App()
    w.show()
    sys.exit(app.exec())
