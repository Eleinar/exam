from PySide6.QtWidgets import QApplication
from main_window import OrderApp
app = QApplication([])
window = OrderApp()
window.show()
app.exec()