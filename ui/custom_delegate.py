# file: ui/custom_delegate.py
from PyQt6.QtWidgets import QStyledItemDelegate, QTextEdit
from PyQt6.QtCore import Qt, QEvent

class MultiLineDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # Khi người dùng muốn sửa, tạo ra một cái khung TextEdit (nhiều dòng)
        editor = QTextEdit(parent)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        return editor

    def setEditorData(self, editor, index):
        # Lấy dữ liệu từ bảng đưa vào khung sửa
        text = index.model().data(index, Qt.ItemDataRole.EditRole)
        if text:
            editor.setText(text)
            # Di chuyển con trỏ xuống cuối văn bản cho tiện
            cursor = editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            editor.setTextCursor(cursor)

    def setModelData(self, editor, model, index):
        # Khi sửa xong, lưu dữ liệu ngược lại vào bảng
        model.setData(index, editor.toPlainText(), Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        # Chỉnh kích thước khung sửa cho vừa vặn với ô
        editor.setGeometry(option.rect)