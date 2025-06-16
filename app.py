from model import model_db
from insert_bd import insert_bd
from config import DATABASE
from product_calculator import calculate_product_output
from flask import Flask, request, render_template, redirect, flash, url_for
import sqlite3
import math
from datetime import datetime
import os
app = Flask(__name__)
app.secret_key = "secret_key_123"



# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    """Главная страница - список материалов с расчетом минимальной партии"""
    if not(os.path.isfile(DATABASE)):
        db = insert_bd()
        db.initialize_database()
        
    conn = get_db_connection()
    
    # Получаем все материалы с информацией о типе
    materials = conn.execute('''
        SELECT m.id, m.name, mt.type_name, m.unit_price, m.stock_quantity, 
               m.min_stock_quantity, m.package_quantity, m.unit_of_measure
        FROM Material m
        JOIN MaterialType mt ON m.type_id = mt.id
    ''').fetchall()
    
    # Рассчитываем стоимость минимальной партии для каждого материала
    materials_with_costs = []
    for material in materials:
        mat_dict = dict(material)
        
        # Расчет стоимости минимальной партии
        if mat_dict['stock_quantity'] < mat_dict['min_stock_quantity']:
            deficit = mat_dict['min_stock_quantity'] - mat_dict['stock_quantity']
            packages_needed = math.ceil(deficit / mat_dict['package_quantity'])
            min_order_quantity = packages_needed * mat_dict['package_quantity']
            min_order_cost = min_order_quantity * mat_dict['unit_price']
            min_order_cost = round(min_order_cost, 2)
        else:
            min_order_quantity = 0
            min_order_cost = 0.0
            
        mat_dict['min_order_quantity'] = min_order_quantity
        mat_dict['min_order_cost'] = min_order_cost
        materials_with_costs.append(mat_dict)
    
    conn.close()
    return render_template("index.html", materials=materials_with_costs)

@app.route("/add_material", methods=["GET", "POST"])
def add_material():
    """Добавление нового материала"""
    conn = get_db_connection()
    
    if request.method == "POST":
        # Получение данных из формы
        name = request.form.get("name")
        type_id = request.form.get("type_id")
        unit_price = request.form.get("unit_price")
        stock_quantity = request.form.get("stock_quantity")
        min_stock_quantity = request.form.get("min_stock_quantity")
        package_quantity = request.form.get("package_quantity")
        unit_of_measure = request.form.get("unit_of_measure")
        
        # Валидация данных
        errors = []
        if not name:
            errors.append("Наименование материала обязательно!")
        if not type_id:
            errors.append("Тип материала обязателен!")
        try:
            unit_price = float(unit_price)
            if unit_price < 0:
                errors.append("Цена не может быть отрицательной!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение цены!")
        try:
            stock_quantity = float(stock_quantity)
            if stock_quantity < 0:
                errors.append("Количество на складе не может быть отрицательным!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение количества на складе!")
        try:
            min_stock_quantity = float(min_stock_quantity)
            if min_stock_quantity < 0:
                errors.append("Минимальный запас не может быть отрицательным!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение минимального запаса!")
        try:
            package_quantity = float(package_quantity)
            if package_quantity <= 0:
                errors.append("Количество в упаковке должно быть больше нуля!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение количества в упаковке!")
        
        if errors:
            for error in errors:
                flash(error, "error")
            material_types = conn.execute("SELECT id, type_name FROM MaterialType").fetchall()
            conn.close()
            return render_template("material_form.html", 
                                  material_types=material_types,
                                  name=name,
                                  type_id=type_id,
                                  unit_price=unit_price,
                                  stock_quantity=stock_quantity,
                                  min_stock_quantity=min_stock_quantity,
                                  package_quantity=package_quantity,
                                  unit_of_measure=unit_of_measure)
        
        # Сохранение в БД
        try:
            conn.execute('''
                INSERT INTO Material (name, type_id, unit_price, stock_quantity, 
                                     min_stock_quantity, package_quantity, unit_of_measure)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, type_id, unit_price, stock_quantity, 
                  min_stock_quantity, package_quantity, unit_of_measure))
            conn.commit()
            flash("Материал успешно добавлен!", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("Материал с таким наименованием уже существует!", "error")
            material_types = conn.execute("SELECT id, type_name FROM MaterialType").fetchall()
            conn.close()
            return render_template("material_form.html", 
                                  material_types=material_types,
                                  name=name,
                                  type_id=type_id,
                                  unit_price=unit_price,
                                  stock_quantity=stock_quantity,
                                  min_stock_quantity=min_stock_quantity,
                                  package_quantity=package_quantity,
                                  unit_of_measure=unit_of_measure)
    
    # GET-запрос - отображение пустой формы
    material_types = conn.execute("SELECT id, type_name FROM MaterialType").fetchall()
    conn.close()
    return render_template("material_form.html", material_types=material_types)

@app.route("/edit_material/<int:material_id>", methods=["GET", "POST"])
def edit_material(material_id):
    """Редактирование существующего материала"""
    conn = get_db_connection()
    
    if request.method == "POST":
        # Получение данных из формы
        name = request.form.get("name")
        type_id = request.form.get("type_id")
        unit_price = request.form.get("unit_price")
        stock_quantity = request.form.get("stock_quantity")
        min_stock_quantity = request.form.get("min_stock_quantity")
        package_quantity = request.form.get("package_quantity")
        unit_of_measure = request.form.get("unit_of_measure")
        
        # Валидация данных (аналогично добавлению)
        errors = []
        if not name:
            errors.append("Наименование материала обязательно!")
        if not type_id:
            errors.append("Тип материала обязателен!")
        try:
            unit_price = float(unit_price)
            if unit_price < 0:
                errors.append("Цена не может быть отрицательной!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение цены!")
        try:
            stock_quantity = float(stock_quantity)
            if stock_quantity < 0:
                errors.append("Количество на складе не может быть отрицательным!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение количества на складе!")
        try:
            min_stock_quantity = float(min_stock_quantity)
            if min_stock_quantity < 0:
                errors.append("Минимальный запас не может быть отрицательным!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение минимального запаса!")
        try:
            package_quantity = float(package_quantity)
            if package_quantity <= 0:
                errors.append("Количество в упаковке должно быть больше нуля!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение количества в упаковке!")
        
        if errors:
            for error in errors:
                flash(error, "error")
            material_types = conn.execute("SELECT id, type_name FROM MaterialType").fetchall()
            return render_template("material_form.html", 
                                  material_types=material_types,
                                  name=name,
                                  type_id=type_id,
                                  unit_price=unit_price,
                                  stock_quantity=stock_quantity,
                                  min_stock_quantity=min_stock_quantity,
                                  package_quantity=package_quantity,
                                  unit_of_measure=unit_of_measure,
                                  material_id=material_id)
        
        # Обновление данных в БД
        try:
            conn.execute('''
                UPDATE Material SET 
                    name = ?,
                    type_id = ?,
                    unit_price = ?,
                    stock_quantity = ?,
                    min_stock_quantity = ?,
                    package_quantity = ?,
                    unit_of_measure = ?
                WHERE id = ?
            ''', (name, type_id, unit_price, stock_quantity, 
                  min_stock_quantity, package_quantity, unit_of_measure, material_id))
            conn.commit()
            flash("Материал успешно обновлен!", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("Материал с таким наименованием уже существует!", "error")
            material_types = conn.execute("SELECT id, type_name FROM MaterialType").fetchall()
            return render_template("material_form.html", 
                                  material_types=material_types,
                                  name=name,
                                  type_id=type_id,
                                  unit_price=unit_price,
                                  stock_quantity=stock_quantity,
                                  min_stock_quantity=min_stock_quantity,
                                  package_quantity=package_quantity,
                                  unit_of_measure=unit_of_measure,
                                  material_id=material_id)
    
    # GET-запрос - загрузка данных материала
    material = conn.execute('''
        SELECT m.id, m.name, m.type_id, m.unit_price, m.stock_quantity, 
               m.min_stock_quantity, m.package_quantity, m.unit_of_measure
        FROM Material m
        WHERE m.id = ?
    ''', (material_id,)).fetchone()
    
    if not material:
        flash("Материал не найден!", "error")
        conn.close()
        return redirect(url_for("index"))
    
    material_types = conn.execute("SELECT id, type_name FROM MaterialType").fetchall()
    conn.close()
    return render_template("material_form.html", 
                           material_types=material_types,
                           **dict(material),
                           material_id=material_id)

@app.route("/material_suppliers/<int:material_id>")
def material_suppliers(material_id):
    """Просмотр поставщиков для конкретного материала"""
    conn = get_db_connection()
    
    # Получаем информацию о материале
    material = conn.execute('''
        SELECT name FROM Material WHERE id = ?
    ''', (material_id,)).fetchone()
    
    if not material:
        flash("Материал не найден!", "error")
        conn.close()
        return redirect(url_for("index"))
    
    # Получаем поставщиков для материала
    suppliers = conn.execute('''
        SELECT s.id, s.name, s.supplier_type, s.rating, s.start_date
        FROM Supplier s
        JOIN MaterialSupplier ms ON s.id = ms.supplier_id
        WHERE ms.material_id = ?
    ''', (material_id,)).fetchall()
    
    conn.close()
    return render_template("material_suppliers.html", 
                           material_name=material['name'],
                           suppliers=suppliers)

@app.route("/calculate_product", methods=["GET", "POST"])
def calculate_product():
    """Расчет количества продукции"""
    conn = get_db_connection()
    
    # Получаем списки типов продукции и материалов
    product_types = conn.execute("SELECT id, type_name FROM ProductType").fetchall()
    material_types = conn.execute("SELECT id, type_name FROM MaterialType").fetchall()
    conn.close()
    
    result = None
    
    if request.method == "POST":
        # Получение данных из формы
        product_type_id = request.form.get("product_type_id")
        material_type_id = request.form.get("material_type_id")
        raw_amount = request.form.get("raw_amount")
        param1 = request.form.get("param1")
        param2 = request.form.get("param2")
        
        # Валидация
        errors = []
        try:
            raw_amount = float(raw_amount or 0)
            param1 = float(param1 or 0)
            param2 = float(param2 or 0)
            
            if raw_amount <= 0:
                errors.append("Количество сырья должно быть положительным!")
            if param1 <= 0:
                errors.append("Параметр 1 должен быть положительным!")
            if param2 <= 0:
                errors.append("Параметр 2 должен быть положительным!")
        except (ValueError, TypeError):
            errors.append("Некорректные входные данные!")
        
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("product_calculator.html", 
                                product_types=product_types,
                                material_types=material_types,
                                product_type_id=product_type_id,
                                material_type_id=material_type_id,
                                raw_amount=raw_amount,
                                param1=param1,
                                param2=param2)
        
        # Используем вынесенный метод расчета
        product_count = calculate_product_output(
            product_type_id, material_type_id, raw_amount, param1, param2
        )
        
        if product_count == -1:
            flash("Ошибка расчета: проверьте введенные данные!", "error")
        else:
            # Получаем дополнительные данные для отображения
            conn = get_db_connection()
            product_coeff = conn.execute('SELECT coefficient FROM ProductType WHERE id = ?', 
                                       (product_type_id,)).fetchone()
            loss_percent = conn.execute('SELECT loss_percent FROM MaterialType WHERE id = ?', 
                                      (material_type_id,)).fetchone()
            conn.close()
            
            # Расчет промежуточных значений
            material_per_unit = param1 * param2 * product_coeff['coefficient']
            required_material_per_unit = material_per_unit / (1 - loss_percent['loss_percent'])
            
            result = {
                "product_count": product_count,
                "raw_amount": raw_amount,
                "param1": param1,
                "param2": param2,
                "product_coeff": product_coeff['coefficient'],
                "loss_percent": loss_percent['loss_percent'],
                "material_per_unit": material_per_unit,
                "required_material_per_unit": required_material_per_unit
            }
    
    # Обязательный возврат ответа в конце функции
    return render_template("product_calculator.html", 
                        product_types=product_types,
                        material_types=material_types,
                        result=result,
                        **request.form if request.method == "POST" else {})
                        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2020, debug=True)
