# ui/drag_list.py
from PyQt6.QtWidgets import QListWidget, QAbstractItemView
from PyQt6.QtCore import pyqtSignal, Qt

class DraggableListWidget(QListWidget):
    # Tín hiệu phát ra khi thứ tự thay đổi hoặc có item bị xóa
    orderChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection) # Cho phép chọn nhiều ảnh để xóa cùng lúc

    def dropEvent(self, event):
        super().dropEvent(event)
        self.orderChanged.emit()

    # --- [MỚI] BẮT SỰ KIỆN BÀN PHÍM ---
    def keyPressEvent(self, event):
        # Kiểm tra nếu phím bấm là Delete
        if event.key() == Qt.Key.Key_Delete:
            # Lấy tất cả các item đang được chọn
            items = self.selectedItems()
            if not items: return
            
            # Xóa từng item khỏi danh sách (nhưng không xóa file gốc)
            for item in items:
                self.takeItem(self.row(item))
            
            # Phát tín hiệu để Main App cập nhật lại bảng bên phải
            self.orderChanged.emit()
        else:
            # Nếu là phím khác thì xử lý như bình thường
            super().keyPressEvent(event)