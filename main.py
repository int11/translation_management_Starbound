import json
import sys

from PyQt5 import QtCore
from PyQt5.Qt import QFileSystemModel
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QWidget, QTreeView, QApplication, QAbstractItemView, QPlainTextEdit, \
    QHBoxLayout, QVBoxLayout
from PyQt5 import QtWidgets
from trans_star import *


class patch_viewer(QTreeView):
    def __init__(self, parent):
        super().__init__(parent)
        self.lines = None
        self.selectindex = None
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.model = QStandardItemModel()

        self.setModel(self.model)
        self.model.setHorizontalHeaderLabels(["path", "value"])
        self.setColumnWidth(0, int(parent.size().width() * 0.2))
        self.setColumnWidth(1, int(parent.size().width() * 0.05))
        self.clicked.connect(self.cil)

        self.koreatext = QPlainTextEdit(parent)
        self.koreatext.textChanged.connect(self.textchange)
        self.originaltext = QPlainTextEdit(parent)
        self.originaltext.setReadOnly(True)

    def reload(self, lines):
        self.lines = lines
        self.model.removeRows(0, self.model.rowCount())
        for e, i in enumerate(lines):
            self.model.insertRow(e)
            self.model.setData(self.model.index(e, 0), i.path)
            self.model.setData(self.model.index(e, 1),
                               i.value if isinstance(i.value, str) else json.dumps(i.value, ensure_ascii=False))

    def textchange(self):
        if not self.selectindex is None:
            value = self.koreatext.toPlainText()
            self.model.setData(self.model.index(self.selectindex, 1), value)
            typ = type(self.lines[self.selectindex].value)
            self.lines[self.selectindex].value = value if typ == str else json.loads(value, strict=False)
            self.lines[self.selectindex].target_patch.save(False)

    def clear(self):
        self.lines = None
        self.selectindex = None
        self.koreatext.clear()
        self.originaltext.clear()
        self.model.removeRows(0, self.model.rowCount())

    @pyqtSlot(QtCore.QModelIndex)
    def cil(self, index):
        self.selectindex = index.row()
        indexitem = self.model.index(index.row(), 1, index.parent())
        self.koreatext.setPlainText(indexitem.data())
        op = self.lines[self.selectindex].op
        if op == 'add':
            self.originaltext.setPlainText("""This line "op" flag is "add" """)
        elif op == 'replace':
            try:
                org = self.lines[self.selectindex].original_value('original')
            except FileNotFoundError as f:
                org = f"""{f}\n\nplease check "assetfile\\original" directory or if not exist download original asset"""
            self.originaltext.setPlainText(org if isinstance(org, str) else json.dumps(org, ensure_ascii=False))
        else:
            print(f"Not consider this line op flag : {op}")
            raise


class explorer(QTreeView):
    def __init__(self, parent, asset):
        super().__init__(parent)

        self.model = QFileSystemModel()
        # set path
        path = parent.assetpath
        self.model.setRootPath(path)
        # set model
        self.setModel(self.model)
        self.setRootIndex(self.model.index(self.model.rootPath()))
        self.setColumnWidth(0, int(parent.size().width() * 0.35))


class Form(QtWidgets.QMainWindow):

    def __init__(self):
        QWidget.__init__(self, flags=Qt.Widget)
        self.assetpath = os.path.abspath('assetfile\\korean')
        self.setWindowTitle("Asset Editer")
        rect = app.desktop().screenGeometry()
        size = (int(rect.height() * 0.8), int(rect.width() * 0.8))
        self.setGeometry(int(rect.height() * 0.1), int(rect.height() * 0.1), size[1], size[0])

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        action0 = QtWidgets.QAction("Open Assset", self)
        action0.triggered.connect(self.action0f)
        action1 = QtWidgets.QAction("Original asset download", self)
        action1.triggered.connect(self.action1f)

        file_menu = menubar.addMenu("File")
        file_menu.addAction(action0)
        file_menu.addAction(action1)

        self.ko_explorer = explorer(self, 'korean')
        self.ko_explorer.clicked.connect(self.cil)
        self.viewer = patch_viewer(self)

        temp = QWidget()
        hbox = QHBoxLayout(temp)
        hbox.addWidget(self.ko_explorer)
        hbox.addWidget(self.viewer)
        vbox = QVBoxLayout(temp)
        vbox.addWidget(self.viewer.koreatext)
        vbox.addWidget(self.viewer.originaltext)
        hbox.addLayout(vbox)
        self.setCentralWidget(temp)

    @pyqtSlot(QtCore.QModelIndex)
    def cil(self, index):
        self.viewer.clear()

        model = self.sender().model
        indexitem = model.index(index.row(), 0, index.parent())
        filename = model.fileName(indexitem)
        filepath = model.filePath(indexitem)
        ex = os.path.splitext(filename)[1]

        if ex == '.patch':
            a = patchfile(filepath[len(self.assetpath) + 1:], self.assetpath)
            lines = [i for i in a.get_lines()]
            self.viewer.reload(lines)

    def action0f(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Asset Folder", '.\\assetfile')
        self.assetpath = path
        self.ko_explorer.model.setRootPath(path)
        self.ko_explorer.setRootIndex(self.ko_explorer.model.index(self.ko_explorer.model.rootPath()))

    def action1f(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Starbound Folder")
        asset.download_original_assets(path)


app = QApplication(sys.argv)
form = Form()
form.show()
sys.exit(app.exec_())
