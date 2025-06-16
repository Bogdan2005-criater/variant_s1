# product_calculator.py
import sqlite3
from config import DATABASE

def calculate_product_output(product_type_id, material_type_id, raw_amount, param1, param2):
    """
    Расчет количества продукции с учетом потерь сырья
    
    Args:
        product_type_id: ID типа продукции
        material_type_id: ID типа материала
        raw_amount: количество используемого сырья
        param1: первый параметр продукции
        param2: второй параметр продукции
    
    Returns:
        int: количество получаемой продукции или -1 при ошибке
    """
    try:
        # Проверка входных данных
        product_type_id = int(product_type_id)
        material_type_id = int(material_type_id)
        raw_amount = float(raw_amount)
        param1 = float(param1)
        param2 = float(param2)
        
        if raw_amount <= 0 or param1 <= 0 or param2 <= 0:
            return -1
            
        # Подключение к БД
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        
        # Получаем коэффициенты из БД
        product_coeff = conn.execute('''
            SELECT coefficient FROM ProductType WHERE id = ?
        ''', (product_type_id,)).fetchone()
        
        loss_percent = conn.execute('''
            SELECT loss_percent FROM MaterialType WHERE id = ?
        ''', (material_type_id,)).fetchone()
        
        # Проверка существования типов
        if not product_coeff or not loss_percent:
            return -1
        
        product_coeff = product_coeff['coefficient']
        loss_percent = loss_percent['loss_percent']
        
        # Рассчитываем количество сырья на единицу продукции
        material_per_unit = param1 * param2 * product_coeff
        
        # Учитываем потери сырья
        required_material_per_unit = material_per_unit / (1 - loss_percent)
        
        # Рассчитываем количество продукции
        product_count = raw_amount / required_material_per_unit
        
        conn.close()
        return int(product_count)  # Целое число
        
    except (ValueError, TypeError, ZeroDivisionError, sqlite3.Error):
        return -1
