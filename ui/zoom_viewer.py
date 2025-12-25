from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsItem, QStyle
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QPen, QColor, QBrush, QPainter, QWheelEvent, QCursor

# ==================================================================================
# CLASS: ResizableRect (Khung xanh có thể chỉnh sửa)
# ==================================================================================
class ResizableRect(QGraphicsRectItem):
    VISUAL_HANDLE_SIZE = 14
    HIT_HANDLE_SIZE = 30
    
    HANDLE_TOP_LEFT = 1
    HANDLE_TOP_MIDDLE = 2
    HANDLE_TOP_RIGHT = 3
    HANDLE_MIDDLE_LEFT = 4
    HANDLE_MIDDLE_RIGHT = 5
    HANDLE_BOTTOM_LEFT = 6
    HANDLE_BOTTOM_MIDDLE = 7
    HANDLE_BOTTOM_RIGHT = 8
    HANDLE_NONE = 0

    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.setPen(QPen(QColor("#00BFFF"), 2, Qt.PenStyle.SolidLine))
        self.setBrush(QBrush(QColor(0, 191, 255, 40)))
        
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | 
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.current_handle = self.HANDLE_NONE
        self.mouse_press_rect = None
        self.mouse_press_pos = None

    def boundingRect(self):
        max_size = max(self.VISUAL_HANDLE_SIZE, self.HIT_HANDLE_SIZE)
        margin = max_size / 2 + 10 
        return self.rect().adjusted(-margin, -margin, margin, margin)

    def get_handle_rects(self, rect, handle_size):
        s = handle_size; s2 = s / 2
        l, t, r, b = rect.left(), rect.top(), rect.right(), rect.bottom()
        cx, cy = rect.center().x(), rect.center().y()
        return {
            self.HANDLE_TOP_LEFT: QRectF(l-s2, t-s2, s, s),
            self.HANDLE_TOP_MIDDLE: QRectF(cx-s2, t-s2, s, s),
            self.HANDLE_TOP_RIGHT: QRectF(r-s2, t-s2, s, s),
            self.HANDLE_MIDDLE_LEFT: QRectF(l-s2, cy-s2, s, s),
            self.HANDLE_MIDDLE_RIGHT: QRectF(r-s2, cy-s2, s, s),
            self.HANDLE_BOTTOM_LEFT: QRectF(l-s2, b-s2, s, s),
            self.HANDLE_BOTTOM_MIDDLE: QRectF(cx-s2, b-s2, s, s),
            self.HANDLE_BOTTOM_RIGHT: QRectF(r-s2, b-s2, s, s),
        }

    def get_handle_at_position(self, pos):
        handles = self.get_handle_rects(self.rect(), self.HIT_HANDLE_SIZE)
        for handle, rect in handles.items():
            if rect.contains(pos): return handle
        return self.HANDLE_NONE

    def hoverMoveEvent(self, event):
        if self.isSelected():
            handle = self.get_handle_at_position(event.pos())
            cursor = Qt.CursorShape.ArrowCursor
            if handle in [self.HANDLE_TOP_LEFT, self.HANDLE_BOTTOM_RIGHT]: cursor = Qt.CursorShape.SizeFDiagCursor
            elif handle in [self.HANDLE_TOP_RIGHT, self.HANDLE_BOTTOM_LEFT]: cursor = Qt.CursorShape.SizeBDiagCursor
            elif handle in [self.HANDLE_TOP_MIDDLE, self.HANDLE_BOTTOM_MIDDLE]: cursor = Qt.CursorShape.SizeVerCursor
            elif handle in [self.HANDLE_MIDDLE_LEFT, self.HANDLE_MIDDLE_RIGHT]: cursor = Qt.CursorShape.SizeHorCursor
            elif handle == self.HANDLE_NONE: cursor = Qt.CursorShape.SizeAllCursor
            self.setCursor(QCursor(cursor))
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if self.isSelected():
            self.current_handle = self.get_handle_at_position(event.pos())
            if self.current_handle != self.HANDLE_NONE:
                self.mouse_press_rect = self.rect()
                self.mouse_press_pos = event.pos()
                return 
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.current_handle != self.HANDLE_NONE:
            rect = self.mouse_press_rect
            pos = event.pos()
            diff = pos - self.mouse_press_pos
            new_x, new_y, new_w, new_h = rect.x(), rect.y(), rect.width(), rect.height()
            
            if self.current_handle == self.HANDLE_TOP_LEFT: new_x += diff.x(); new_w -= diff.x(); new_y += diff.y(); new_h -= diff.y()
            elif self.current_handle == self.HANDLE_TOP_MIDDLE: new_y += diff.y(); new_h -= diff.y()
            elif self.current_handle == self.HANDLE_TOP_RIGHT: new_w += diff.x(); new_y += diff.y(); new_h -= diff.y()
            elif self.current_handle == self.HANDLE_MIDDLE_LEFT: new_x += diff.x(); new_w -= diff.x()
            elif self.current_handle == self.HANDLE_MIDDLE_RIGHT: new_w += diff.x()
            elif self.current_handle == self.HANDLE_BOTTOM_LEFT: new_x += diff.x(); new_w -= diff.x(); new_h += diff.y()
            elif self.current_handle == self.HANDLE_BOTTOM_MIDDLE: new_h += diff.y()
            elif self.current_handle == self.HANDLE_BOTTOM_RIGHT: new_w += diff.x(); new_h += diff.y()
            
            if new_w < 20: new_w = 20
            if new_h < 20: new_h = 20
            
            self.prepareGeometryChange() 
            self.setRect(new_x, new_y, new_w, new_h)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.current_handle = self.HANDLE_NONE
        super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget=None):
        option.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(QColor("#00BFFF"), 1, Qt.PenStyle.SolidLine))
            painter.setBrush(QBrush(QColor("white")))
            handles = self.get_handle_rects(self.rect(), self.VISUAL_HANDLE_SIZE)
            for handle_rect in handles.values(): painter.drawRect(handle_rect)

# ==================================================================================
# CLASS: PhotoViewer (Trình xem ảnh chính)
# ==================================================================================
class PhotoViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) 
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self._pixmap_item = None
        self._is_drawing = False
        self._draw_start_point = None
        self._temp_rubber_band = None 

    # --- SỬA HÀM NÀY ĐỂ HỖ TRỢ GIỮ ZOOM ---
    def set_image(self, pixmap: QPixmap, maintain_zoom=False):
        # Lưu trạng thái zoom hiện tại nếu được yêu cầu
        old_transform = self.transform()
        has_old_image = self._pixmap_item is not None

        self.scene.clear()
        self._pixmap_item = self.scene.addPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))
        
        # Logic: Nếu maintain_zoom=True VÀ trước đó đã có ảnh -> Khôi phục zoom
        if maintain_zoom and has_old_image:
            self.setTransform(old_transform)
        else:
            # Nếu không (lần đầu mở hoặc reset) -> Fit to View
            self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
        self.reset_mode()

    def reset_mode(self):
        self._is_drawing = False
        self._draw_start_point = None
        if self._temp_rubber_band:
            self.scene.removeItem(self._temp_rubber_band)
            self._temp_rubber_band = None
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def add_manual_rect(self):
        if self._pixmap_item is None: return
        self._is_drawing = True
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor) 

    def mousePressEvent(self, event):
        if self._is_drawing and event.button() == Qt.MouseButton.LeftButton:
            self._draw_start_point = self.mapToScene(event.pos())
            self._temp_rubber_band = QGraphicsRectItem()
            self._temp_rubber_band.setPen(QPen(QColor("#00BFFF"), 2, Qt.PenStyle.SolidLine))
            self._temp_rubber_band.setBrush(QBrush(QColor(0, 191, 255, 40)))
            self.scene.addItem(self._temp_rubber_band)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_drawing and self._draw_start_point and self._temp_rubber_band:
            current_point = self.mapToScene(event.pos())
            rect = QRectF(self._draw_start_point, current_point).normalized()
            self._temp_rubber_band.setRect(rect)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_drawing and self._draw_start_point and event.button() == Qt.MouseButton.LeftButton:
            end_point = self.mapToScene(event.pos())
            rect_f = QRectF(self._draw_start_point, end_point).normalized()

            if self._temp_rubber_band:
                self.scene.removeItem(self._temp_rubber_band)
                self._temp_rubber_band = None

            if rect_f.width() > 10 and rect_f.height() > 10:
                self.add_rect(rect_f.x(), rect_f.y(), rect_f.width(), rect_f.height())

            self.reset_mode()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoomIn = 1.15
            if event.angleDelta().y() > 0: self.scale(zoomIn, zoomIn)
            else: self.scale(1/zoomIn, 1/zoomIn)
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        else:
            super().keyPressEvent(event)

    def add_rect(self, x, y, w, h):
        self.scene.addItem(ResizableRect(x, y, w, h))

    def get_rects(self):
        rects = []
        for item in self.scene.items():
            if isinstance(item, ResizableRect):
                pos = item.scenePos()
                r = item.rect()
                rects.append((int(pos.x()+r.x()), int(pos.y()+r.y()), int(r.width()), int(r.height())))
        return rects

    def clear_rects(self):
        for item in self.scene.items():
            if isinstance(item, ResizableRect): self.scene.removeItem(item)

    def delete_selected(self):
        for item in self.scene.selectedItems():
            if isinstance(item, ResizableRect): self.scene.removeItem(item)