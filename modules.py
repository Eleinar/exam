from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Boolean,
    ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Statuses(Base):
        __tablename__ = "statuses"

        id = Column(Integer, primary_key = True)
        status = Column(String)

class Clients(Base):
        __tablename__ = "clients"

        id = Column(Integer, primary_key = True)
        client_name = Column(String)

class Goods(Base):
        __tablename__ = "goods"

        id = Column(Integer, primary_key = True)
        good_name = Column(String)

class Orders(Base):
        __tablename__ = "orders"
        
        id = Column(Integer, primary_key = True)
        id_client = Column(Integer, ForeignKey(Clients.id))
        order_status = Column(Integer, ForeignKey(Statuses.id))
        order_date = Column(Date)

        client_rel = relationship("Clients")
        status_rel = relationship("Statuses")

class Orders_Goods(Base):
        __tablename__ = "orders_goods"

        id = Column(Integer, primary_key = True)

        id_good = Column(Integer, ForeignKey(Goods.id))
        id_order = Column(Integer, ForeignKey(Orders.id))

        good_rel = relationship("Goods")
        order_rel = relationship("Orders")

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey(Orders.id))
    old_status = Column(Integer, ForeignKey(Statuses.id))
    new_status = Column(Integer, ForeignKey(Statuses.id))
    change_date = Column(Date)

    order_rel = relationship("Orders")
    old_status_rel = relationship("Statuses", foreign_keys=[old_status])
    new_status_rel = relationship("Statuses", foreign_keys=[new_status])

    



def create_connection():
        engine = create_engine("postgresql://postgres@localhost:5432/Orders")  # Создание движка для подключения к базе данных
        Base.metadata.create_all(engine)  # Создание всех таблиц, если они не существуют
        Session = sessionmaker(bind=engine)  # Создание фабрики сессий
        session = Session()  # Создание новой сессии
        return session  # Возврат сессии