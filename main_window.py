from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox
)

from PySide6.QtGui import QIcon
from sqlalchemy.orm import joinedload
from datetime import date

from modules import Orders, Statuses, Clients, Goods, Orders_Goods, OrderStatusHistory, create_connection


class OrderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление заказами")
        self.setWindowIcon(QIcon("mrpenis.jpeg"))
        self.db = create_connection()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Add order section
        add_order_layout = QHBoxLayout()
        self.client_input = QLineEdit()
        self.client_input.setPlaceholderText("Клиент")
        self.good_input = QLineEdit()
        self.good_input.setPlaceholderText("Товары")
        self.add_order_button = QPushButton("Добавить заказ")
        self.add_order_button.clicked.connect(self.add_order)

        add_order_layout.addWidget(QLabel("Добавить заказ:"))
        add_order_layout.addWidget(self.client_input)
        add_order_layout.addWidget(self.good_input)
        add_order_layout.addWidget(self.add_order_button)

        main_layout.addLayout(add_order_layout)

        # Update order status section
        update_status_layout = QHBoxLayout()
        self.order_id_input = QLineEdit()
        self.order_id_input.setPlaceholderText("ID заказа")
        self.status_combo = QComboBox()
        self.load_statuses()
        self.update_status_button = QPushButton("Обновить статус")
        self.update_status_button.clicked.connect(self.update_status)
        update_status_layout.addWidget(QLabel("Обновление статуса заказа:"))
        update_status_layout.addWidget(self.order_id_input)
        update_status_layout.addWidget(self.status_combo)
        update_status_layout.addWidget(self.update_status_button)
        main_layout.addLayout(update_status_layout)

        # Orders table
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(4)
        self.orders_table.setHorizontalHeaderLabels(["ID заказа", "Клиент", "Статус", "Дата"])
        main_layout.addWidget(self.orders_table)

        # History section
        history_layout = QHBoxLayout()
        self.history_order_id_input = QLineEdit()
        self.history_order_id_input.setPlaceholderText("ID заказа")
        self.history_button = QPushButton("Показать историю")
        self.history_button.clicked.connect(self.show_history)
        history_layout.addWidget(QLabel("История статусов:"))
        history_layout.addWidget(self.history_order_id_input)
        history_layout.addWidget(self.history_button)
        main_layout.addLayout(history_layout)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Дата изменения", "Старый статус", "Новый статус", "ID заказа"])
        main_layout.addWidget(self.history_table)


        # Main container
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Refresh orders to display all at start
        self.refresh_orders()

    def load_statuses(self):
        statuses = self.db.query(Statuses).all()
        self.status_combo.addItems([status.status for status in statuses])

    def add_order(self):
        client_name = self.client_input.text()
        goods_names = self.good_input.text().split(",")

        if not client_name or not goods_names:
            return

        client = self.db.query(Clients).filter_by(client_name=client_name).first()
        if not client:
            client = Clients(client_name=client_name)
            self.db.add(client)
            self.db.commit()

        order = Orders(id_client=client.id, order_status=1, order_date=date.today())
        self.db.add(order)
        self.db.commit()

        for good_name in goods_names:
            good = self.db.query(Goods).filter_by(good_name=good_name.strip()).first()
            if not good:
                good = Goods(good_name=good_name.strip())
                self.db.add(good)
                self.db.commit()

            order_good = Orders_Goods(id_order=order.id, id_good=good.id)
            self.db.add(order_good)
            self.db.commit()

        self.client_input.clear()
        self.good_input.clear()
        self.refresh_orders()

    def update_status(self):
        order_id = self.order_id_input.text()
        new_status = self.status_combo.currentText()

        order = self.db.query(Orders).filter_by(id=order_id).first()
        if order:
            current_status_id = order.order_status
            status = self.db.query(Statuses).filter_by(status=new_status).first()
            order.order_status = status.id
            self.db.commit()

            # Запись в историю изменений статуса
            history_entry = OrderStatusHistory(
                order_id=order.id,
                old_status=current_status_id,
                new_status=status.id,
                change_date=date.today(),
            )
            self.db.add(history_entry)
            self.db.commit()

            self.refresh_orders()

    def search_orders(self):
        query = self.search_input.text()
        if not query:
            self.refresh_orders()
            return

        search_type = self.search_criteria.currentText()
        if search_type == "ID заказа":
            results = self.db.query(Orders).filter(Orders.id == query).options(joinedload(Orders.client_rel)).all()
        elif search_type == "Имя клиента":
            results = self.db.query(Orders).join(Clients).filter(Clients.client_name.contains(query)).options(joinedload(Orders.client_rel)).all()
        else:
            results = []
        self.display_orders(results)

    def refresh_orders(self):
        orders = self.db.query(Orders).options(joinedload(Orders.client_rel)).all()
        self.display_orders(orders)

    def display_orders(self, orders):
        self.orders_table.setRowCount(0)
        for row, order in enumerate(orders):
            self.orders_table.insertRow(row)
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.client_rel.client_name))
            self.orders_table.setItem(row, 2, QTableWidgetItem(self.get_status_name(order.order_status)))
            self.orders_table.setItem(row, 3, QTableWidgetItem(order.order_date.strftime("%Y-%m-%d")))

    def get_status_name(self, status_id):
        status = self.db.query(Statuses).filter_by(id=status_id).first()
        return status.status if status else "Неизвестно"

    def display_history(self, history_entries):
        self.history_table.setRowCount(0)
        for row, entry in enumerate(history_entries):
            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QTableWidgetItem(entry.change_date.strftime("%Y-%m-%d")))
            self.history_table.setItem(row, 1, QTableWidgetItem(entry.old_status_rel.status if entry.old_status_rel else "Неизвестно"))
            self.history_table.setItem(row, 2, QTableWidgetItem(entry.new_status_rel.status if entry.new_status_rel else "Неизвестно"))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(entry.order_id)))

    def show_history(self):
        order_id = self.history_order_id_input.text()
        if not order_id:
            return

        history_entries = (
            self.db.query(OrderStatusHistory)
            .filter_by(order_id=order_id)
            .options(
                joinedload(OrderStatusHistory.old_status_rel),
                joinedload(OrderStatusHistory.new_status_rel),
            )
            .all()
        )

        self.display_history(history_entries)

