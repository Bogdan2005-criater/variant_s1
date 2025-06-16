# product_calculator.py
import sqlite3
from config import DATABASE

def calculate_product_output(product_type_id, material_type_id, raw_amount, param1, param2):
    """
    Расчет количества продукции с учетом потерь сырья
    
    Args:
        product_type_id: ID типа продукции (должен существовать в БД)
        material_type_id: ID типа материала (должен существовать в БД)
        raw_amount: количество используемого сырья (положительное число)
        param1: первый параметр продукции (положительное число)
        param2: второй параметр продукции (положительное число)
    
    Returns:
        int: количество получаемой продукции (округляется вниз) или -1 при ошибке
    """
    try:
        # Проверка и преобразование входных данных
        product_type_id = int(product_type_id)
        material_type_id = int(material_type_id)
        raw_amount = float(raw_amount)
        param1 = float(param1)
        param2 = float(param2)
        
        # Проверка на положительные значения
        if raw_amount <= 0 or param1 <= 0 or param2 <= 0:
            raise ValueError("Все числовые параметры должны быть положительными")
            
        # Подключение к БД
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            
            # Проверка существования типа продукции
            product_coeff = conn.execute('''
                SELECT coefficient FROM ProductType WHERE id = ?
            ''', (product_type_id,)).fetchone()
            
            if not product_coeff:
                raise ValueError("Тип продукции с указанным ID не найден")
            
            # Проверка существования типа материала
            loss_percent = conn.execute('''
                SELECT loss_percent FROM MaterialType WHERE id = ?
            ''', (material_type_id,)).fetchone()
            
            if not loss_percent:
                raise ValueError("Тип материала с указанным ID не найден")
            
            product_coeff = product_coeff['coefficient']
            loss_percent = loss_percent['loss_percent']
            
            # Дополнительная проверка на корректность коэффициентов
            if product_coeff <= 0 or not (0 <= loss_percent < 1):
                raise ValueError("Некорректные коэффициенты в базе данных")
            
            # Рассчитываем количество сырья на единицу продукции
            material_per_unit = param1 * param2 * product_coeff
            
            # Учитываем потери сырья (защита от деления на 0)
            if loss_percent >= 1:
                raise ValueError("Процент потерь должен быть меньше 1")
                
            required_material_per_unit = material_per_unit / (1 - loss_percent)
            
            # Рассчитываем количество продукции (округляем вниз)
            product_count = raw_amount / required_material_per_unit
            
            return int(product_count)  # Целое число (округление вниз)
        
    except (ValueError, TypeError) as e:
        print(f"Ошибка ввода: {str(e)}")
        return -1
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {str(e)}")
        return -1
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")
        return -1

# Пример использования
if __name__ == "__main__":
    # Тестовый вызов с корректными параметрами (должен вернуть положительное число)
    print("Тест 1 (корректные параметры):", 
          calculate_product_output(1, 1, 1000.0, 2.0, 3.0))
    
    # Тест с несуществующим ID типа продукции (должен вернуть -1)
    print("Тест 2 (несуществующий тип продукции):", 
          calculate_product_output(999, 1, 1000.0, 2.0, 3.0))
    
    # Тест с отрицательным количеством сырья (должен вернуть -1)
    print("Тест 3 (отрицательное сырье):", 
          calculate_product_output(1, 1, -1000.0, 2.0, 3.0))
