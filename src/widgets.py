from PySide6.QtWidgets import (
    QComboBox, QSpinBox, QStyleOptionSpinBox, QStyle, QDialog,
    QVBoxLayout, QLabel, QProgressBar, QWidget, QLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QColor

# ---------- ModernComboBox ----------
class ModernComboBox(QComboBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#6b7280"))
        font = self.font()
        font.setPixelSize(10)
        painter.setFont(font)
        rect = self.rect()
        painter.drawText(
            rect.adjusted(0, 0, -10, 0),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "▼",
        )

# ---------- ModernSpinBox ----------
class ModernSpinBox(QSpinBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = self.font()
        font.setPixelSize(10)
        painter.setFont(font)
        opt = QStyleOptionSpinBox()
        self.initStyleOption(opt)

        up_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_SpinBox, opt, QStyle.SubControl.SC_SpinBoxUp, self
        )
        down_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_SpinBox,
            opt,
            QStyle.SubControl.SC_SpinBoxDown,
            self,
        )

        draw_up_rect = up_rect.translated(0, 2)
        draw_down_rect = down_rect.translated(0, -2)

        up_pressed = opt.activeSubControls == QStyle.SubControl.SC_SpinBoxUp and (
            opt.state & QStyle.StateFlag.State_Sunken
        )
        down_pressed = opt.activeSubControls == QStyle.SubControl.SC_SpinBoxDown and (
            opt.state & QStyle.StateFlag.State_Sunken
        )

        painter.setPen(QColor("#0078d4") if up_pressed else QColor("#4b5563"))
        painter.drawText(draw_up_rect, Qt.AlignmentFlag.AlignCenter, "▲")
        painter.setPen(QColor("#0078d4") if down_pressed else QColor("#4b5563"))
        painter.drawText(draw_down_rect, Qt.AlignmentFlag.AlignCenter, "▼")

# ---------- FlowLayout ----------
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=-1, hspacing=-1, vspacing=-1):
        super(FlowLayout, self).__init__(parent)
        self._item_list = []
        self._hspacing = hspacing
        self._vspacing = vspacing
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def horizontalSpacing(self):
        return (
            self._hspacing
            if self._hspacing >= 0
            else self.smartSpacing(QStyle.PixelMetric.PM_LayoutHorizontalSpacing)
        )

    def verticalSpacing(self):
        return (
            self._vspacing
            if self._vspacing >= 0
            else self.smartSpacing(QStyle.PixelMetric.PM_LayoutVerticalSpacing)
        )

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        return self._item_list[index] if 0 <= index < len(self._item_list) else None

    def takeAt(self, index):
        return self._item_list.pop(index) if 0 <= index < len(self._item_list) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.calculateHeight(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.calculateHeight(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(
            margins.left() + margins.right(), margins.top() + margins.bottom()
        )

    def calculateHeight(self, rect, testOnly):
        margins = self.contentsMargins()
        effective = rect.adjusted(
            margins.left(), margins.top(), -margins.right(), -margins.bottom()
        )
        x, y = effective.x(), effective.y()
        lineHeight = 0
        for item in self._item_list:
            widget = item.widget()
            spaceX = self.horizontalSpacing()
            if spaceX == -1:
                spaceX = widget.style().layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Horizontal,
                )
            spaceY = self.verticalSpacing()
            if spaceY == -1:
                spaceY = widget.style().layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Vertical,
                )
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > effective.right() and lineHeight > 0:
                x, y = effective.x(), y + lineHeight + spaceY
                nextX, lineHeight = x + item.sizeHint().width() + spaceX, 0
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x, lineHeight = nextX, max(lineHeight, item.sizeHint().height())
        return y + lineHeight - rect.y() + margins.bottom()

    def smartSpacing(self, pm):
        parent = self.parent()
        if not parent:
            return -1
        if isinstance(parent, QWidget):
            return parent.style().pixelMetric(pm, None, parent)
        elif isinstance(parent, QLayout):
            return parent.spacing()
        return -1

# ---------- SimpleProgressDialog ----------
class SimpleProgressDialog(QDialog):
    def __init__(self, title, message, save_dir=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(360, 130)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 10px; }
        """)
        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2,
                parent.y() + (parent.height() - self.height()) // 2,
            )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 11pt; color: #1f2937; font-weight: bold;")
        layout.addWidget(label)

        if save_dir:
            dir_label = QLabel(f"保存到：{save_dir}")
            dir_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dir_label.setStyleSheet("font-size: 9pt; color: #6b7280;")
            dir_label.setWordWrap(True)
            layout.addWidget(dir_label)

        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setStyleSheet("""
            QProgressBar { border: none; border-radius: 4px; background-color: #f3f4f6; height: 6px; }
            QProgressBar::chunk { background-color: #0078d4; border-radius: 4px; }
        """)
        layout.addWidget(progress)