from PySide6.QtWidgets import QFrame, QGridLayout, QWidget


class GridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QGridLayout(self)
        self.cells = []
        self._init_grid()

    def _init_grid(self):
        for i in range(3):
            for j in range(3):
                frame = QFrame()
                frame.setFrameShape(QFrame.Shape.Box)
                frame.setStyleSheet(
                    "background-color: #f0f0f0; border: 2px solid #ccc; border-radius: 8px;"
                )
                frame.setFixedSize(100, 100)
                self._layout.addWidget(frame, i, j)
                self.cells.append(frame)

    def highlight(self, index: int):
        self.clear()
        if 0 <= index < len(self.cells):
            self.cells[index].setStyleSheet(
                "background-color: #3498db; border: 2px solid #2980b9; border-radius: 8px;"
            )

    def clear(self):
        for cell in self.cells:
            cell.setStyleSheet(
                "background-color: #f0f0f0; border: 2px solid #ccc; border-radius: 8px;"
            )
