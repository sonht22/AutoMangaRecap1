# ui/panel_dock.py
from PyQt6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QGroupBox, 
                             QSpinBox, QPushButton, QRadioButton, QFormLayout)
from PyQt6.QtCore import Qt

class PanelDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Panel Operations", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        
        content = QWidget()
        layout = QVBoxLayout(content)

        # --- NHÓM 1: PANEL DETECTION SETTINGS (GIỐNG ẢNH MẪU) ---
        group_detect = QGroupBox("Panel Detection Settings")
        form_layout = QFormLayout()
        
        # Width Adjustment (Cho phép số âm)
        self.spin_width_adj = QSpinBox()
        self.spin_width_adj.setRange(-100, 100) # Từ -100 đến +100
        self.spin_width_adj.setValue(0)         # Mặc định 0
        self.spin_width_adj.setSuffix(" px")
        self.spin_width_adj.setToolTip("Số DƯƠNG: Mở rộng vùng cắt.\nSố ÂM: Thu nhỏ vùng cắt (cắt bớt viền trắng).")
        
        # Height Adjustment
        self.spin_height_adj = QSpinBox()
        self.spin_height_adj.setRange(-100, 100)
        self.spin_height_adj.setValue(0)
        self.spin_height_adj.setSuffix(" px")
        
        form_layout.addRow("Width Adjustment:", self.spin_width_adj)
        form_layout.addRow("Height Adjustment:", self.spin_height_adj)
        group_detect.setLayout(form_layout)
        
        # --- NHÓM 2: PANEL CUTTING SETTINGS ---
        group_cut = QGroupBox("Panel Cutting Settings")
        v_layout = QVBoxLayout()
        
        self.radio_top_bottom = QRadioButton("Top to Bottom")
        self.radio_top_bottom.setChecked(True)
        self.radio_left_right = QRadioButton("Left to Right")
        
        v_layout.addWidget(self.radio_top_bottom)
        v_layout.addWidget(self.radio_left_right)
        group_cut.setLayout(v_layout)

        # --- NÚT CẮT ---
        self.btn_cut_trigger = QPushButton("✂️ Cut Panels")
        self.btn_cut_trigger.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b; color: white; padding: 12px; 
                font-weight: bold; border-radius: 4px; font-size: 14px;
            }
            QPushButton:hover { background-color: #444; }
        """)

        layout.addWidget(group_detect)
        layout.addWidget(group_cut)
        layout.addWidget(self.btn_cut_trigger)
        layout.addStretch()

        content.setLayout(layout)
        self.setWidget(content)