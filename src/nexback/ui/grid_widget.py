"""3x3 grid widget for displaying position stimuli in the training game.

This module provides the visual representation of the 9-cell grid used
for position-based stimuli in the Dual N-Back training task.
"""

from PySide6.QtWidgets import QFrame, QGridLayout, QWidget


class GridWidget(QWidget):
    """3x3 grid display for position stimulus presentation.

    Provides visual highlighting of cells to indicate current position stimulus
    during the training session.
    """

    # Style constants
    CELL_INACTIVE_STYLE = (
        "background-color: #f0f0f0; border: 2px solid #ccc; border-radius: 8px;"
    )
    CELL_ACTIVE_STYLE = (
        "background-color: #3498db; border: 2px solid #2980b9; border-radius: 8px;"
    )
    CELL_SIZE = 100

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the grid widget.

        Args:
            parent: Parent widget, if any.
        """
        super().__init__(parent)
        self._layout = QGridLayout(self)
        self.cells: list[QFrame] = []
        self._init_grid()

    def _init_grid(self) -> None:
        """Create and initialize 9 grid cells in 3x3 layout."""
        for i in range(3):
            for j in range(3):
                frame = QFrame()
                frame.setFrameShape(QFrame.Shape.Box)
                frame.setStyleSheet(self.CELL_INACTIVE_STYLE)
                frame.setFixedSize(self.CELL_SIZE, self.CELL_SIZE)
                self._layout.addWidget(frame, i, j)
                self.cells.append(frame)

    def highlight(self, index: int) -> None:
        """Highlight a specific cell by index.

        Args:
            index: Cell index (0-8) to highlight.
        """
        self.clear()
        if 0 <= index < len(self.cells):
            self.cells[index].setStyleSheet(self.CELL_ACTIVE_STYLE)

    def clear(self) -> None:
        """Reset all cells to inactive state."""
        for cell in self.cells:
            cell.setStyleSheet(self.CELL_INACTIVE_STYLE)
