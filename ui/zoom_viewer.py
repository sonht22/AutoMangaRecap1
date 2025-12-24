from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QWheelEvent, QPainter

class PhotoViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        
        # --- CẤU HÌNH GIAO DIỆN ---
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # BẬT THANH CUỘN (Để lăn chuột cuộn trang được)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn) 
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        self.setBackgroundBrush(Qt.GlobalColor.black) 
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        
        # Chế độ kéo bằng tay (Giữ chuột trái kéo ảnh)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) 
        
        # Render mượt hơn
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    def has_photo(self):
        return not self._empty

    def set_photo(self, pixmap: QPixmap = None):
        # Hàm này quyết định xem có reset Zoom hay không khi chuyển ảnh
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
            
            # [LOGIC GIỮ ZOOM]
            # Chỉ Fit vào khung khi _zoom đang là 0 (tức là chưa ai phóng to cả)
            if self._zoom == 0:
                self.fitInView(self._photo, Qt.AspectRatioMode.KeepAspectRatio)
            # Nếu _zoom != 0 (đang phóng to), thì KHÔNG làm gì cả -> Giữ nguyên tỷ lệ cũ
            
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._photo.setPixmap(QPixmap())
            self._zoom = 0 # Không có ảnh thì reset

    def wheelEvent(self, event: QWheelEvent):
        if self.has_photo():
            # [LOGIC PHÂN BIỆT ZOOM VÀ CUỘN]
            
            # Kiểm tra xem phím Ctrl có đang được nhấn không
            modifiers = event.modifiers()
            
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                # --- CÓ Ctrl -> THỰC HIỆN ZOOM ---
                if event.angleDelta().y() > 0:
                    factor = 1.25
                    self._zoom += 1
                else:
                    factor = 0.8
                    self._zoom -= 1
                
                if self._zoom > 0:
                    self.scale(factor, factor)
                elif self._zoom == 0:
                    self.fitInView(self._photo, Qt.AspectRatioMode.KeepAspectRatio)
                else:
                    # Không cho zoom nhỏ hơn kích thước gốc quá nhiều
                    self._zoom = 0
                    self.fitInView(self._photo, Qt.AspectRatioMode.KeepAspectRatio)
            
            else:
                # --- KHÔNG CÓ Ctrl -> THỰC HIỆN CUỘN TRANG (Mặc định) ---
                # Gọi hàm gốc của QGraphicsView để nó tự xử lý thanh cuộn
                super().wheelEvent(event)