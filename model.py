import pandas as pd
import sqlite3
from datetime import datetime
from config import DATABASE
from flask import g

class model_db:
    def __init__(self):
        self.name_db = DATABASE
    
    def init_db(self):
        """Инициализация соединения с базой данных"""
        if "db" not in g:
            g.db = sqlite3.connect(self.name_db)
            g.db.row_factory = sqlite3.Row
        return g.db

    def create_tables(self):
        """Создание таблиц в базе данных"""
        db = self.init_db()
        cursor = db.cursor()
        
        try:
            cursor.executescript('''
            CREATE TABLE IF NOT EXISTS MaterialType (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT NOT NULL UNIQUE,
                loss_percent REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ProductType (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT NOT NULL UNIQUE,
                coefficient REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Supplier (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                supplier_type TEXT NOT NULL,
                inn TEXT NOT NULL UNIQUE,
                rating INTEGER NOT NULL,
                start_date DATE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Material (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type_id INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                stock_quantity REAL NOT NULL,
                min_stock_quantity REAL NOT NULL,
                package_quantity REAL NOT NULL,
                unit_of_measure TEXT NOT NULL,
                FOREIGN KEY (type_id) REFERENCES MaterialType(id)
            );

            CREATE TABLE IF NOT EXISTS MaterialSupplier (
                material_id INTEGER NOT NULL,
                supplier_id INTEGER NOT NULL,
                PRIMARY KEY (material_id, supplier_id),
                FOREIGN KEY (material_id) REFERENCES Material(id),
                FOREIGN KEY (supplier_id) REFERENCES Supplier(id)
            );
            ''')
            db.commit()
            print("Таблицы успешно созданы")
        except sqlite3.Error as e:
            print(f"Ошибка при создании таблиц: {e}")
        finally:
            cursor.close()

    @staticmethod
    def convert_date(date_str):
        """Преобразование даты из строки в объект date"""
        if isinstance(date_str, str):
            return datetime.strptime(date_str.split()[0], '%Y-%m-%d').date()
        return date_str

    def load_initial_data(self):
        """Загрузка начальных данных из Excel-файлов"""
        db = self.init_db()
        
        try:
            # 1. Загрузка типов материалов
            material_type_df = pd.read_excel('data/Material_type_import.xlsx')
            material_type_df.columns = ['type_name', 'loss_percent']
            material_type_df.to_sql('MaterialType', db, if_exists='append', index=False)

            # 2. Загрузка типов продукции
            product_type_df = pd.read_excel('data/Product_type_import.xlsx')
            product_type_df.columns = ['type_name', 'coefficient']
            product_type_df.to_sql('ProductType', db, if_exists='append', index=False)

            # 3. Загрузка поставщиков
            suppliers_df = pd.read_excel('data/Suppliers_import.xlsx')
            suppliers_df.columns = ['name', 'supplier_type', 'inn', 'rating', 'start_date']
            suppliers_df['start_date'] = suppliers_df['start_date'].apply(self.convert_date)
            suppliers_df.to_sql('Supplier', db, if_exists='append', index=False)

            # 4. Загрузка материалов
            materials_df = pd.read_excel('data/Materials_import.xlsx')
            materials_df.columns = [
                'name', 'type_name', 'unit_price', 'stock_quantity', 
                'min_stock_quantity', 'package_quantity', 'unit_of_measure'
            ]

            # Получаем соответствие типов материалов и их ID
            type_map = pd.read_sql('SELECT id, type_name FROM MaterialType', db)
            materials_df = pd.merge(materials_df, type_map, on='type_name')
            materials_df = materials_df.drop(columns=['type_name']).rename(columns={'id': 'type_id'})
            materials_df.to_sql('Material', db, if_exists='append', index=False)

            # 5. Загрузка связей материал-поставщик
            supply_df = pd.read_excel('data/Material_suppliers_import.xlsx')
            supply_df.columns = ['material_name', 'supplier_name']

            # Получаем ID материалов
            materials_map = pd.read_sql('SELECT id, name FROM Material', db)
            supply_df = pd.merge(supply_df, materials_map, 
                                left_on='material_name', 
                                right_on='name').drop(columns=['name', 'material_name'])

            # Получаем ID поставщиков
            suppliers_map = pd.read_sql('SELECT id, name FROM Supplier', db)
            supply_df = pd.merge(supply_df, suppliers_map, 
                                left_on='supplier_name', 
                                right_on='name').drop(columns=['name', 'supplier_name'])

            supply_df.columns = ['material_id', 'supplier_id']
            supply_df.to_sql('MaterialSupplier', db, if_exists='append', index=False)

            # Создание индексов
            cursor = db.cursor()
            cursor.executescript('''
            CREATE INDEX IF NOT EXISTS idx_material_type ON Material(type_id);
            CREATE INDEX IF NOT EXISTS idx_supplier_material ON MaterialSupplier(material_id);
            CREATE INDEX IF NOT EXISTS idx_material_supplier ON MaterialSupplier(supplier_id);
            ''')
            db.commit()
            print("Данные успешно загружены в базу данных")
            
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()

    def initialize_database(self):
        """Полная инициализация базы данных (создание таблиц и загрузка данных)"""
        self.create_tables()
        self.load_initial_data()

    @staticmethod
    def close_db(e=None):
        """Закрытие соединения с базой данных"""
        db = g.pop('db', None)
        if db is not None:
            db.close()
