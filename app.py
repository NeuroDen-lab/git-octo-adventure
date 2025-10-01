from flask import Flask, render_template, request, redirect, url_for, flash, session
import random
import re
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # В продакшене используйте более безопасный ключ

# Функция для валидации номера карты (алгоритм Луна)
def luhn_check(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10 == 0

# Функция для определения типа карты
def get_card_type(card_number):
    card_number = card_number.replace(' ', '')
    if card_number.startswith('4'):
        return 'Visa'
    elif card_number.startswith('5') or card_number.startswith('2'):
        return 'Mastercard'
    elif card_number.startswith('3'):
        return 'American Express'
    else:
        return 'Unknown'

# Функция для валидации срока действия карты
def validate_expiry(expiry):
    try:
        month, year = expiry.split('/')
        month = int(month)
        year = int('20' + year)
        
        if month < 1 or month > 12:
            return False
            
        current_date = datetime.now()
        expiry_date = datetime(year, month, 1)
        
        return expiry_date > current_date
    except:
        return False

# Функция для симуляции обработки платежа
def process_payment(card_number, expiry, cvv, amount=100.00):
    # Очищаем номер карты от пробелов
    clean_card_number = card_number.replace(' ', '')
    
    # Проверяем базовые условия
    if len(clean_card_number) != 16 or not clean_card_number.isdigit():
        return {"success": False, "error": "Неверный номер карты"}
    
    if not luhn_check(clean_card_number):
        return {"success": False, "error": "Неверный номер карты"}
    
    if not validate_expiry(expiry):
        return {"success": False, "error": "Карта просрочена"}
    
    if len(cvv) != 3 or not cvv.isdigit():
        return {"success": False, "error": "Неверный CVV код"}
    
    # Симуляция различных сценариев отказа
    failure_scenarios = [
        {"success": False, "error": "Недостаточно средств"},
        {"success": False, "error": "Карта заблокирована"},
        {"success": False, "error": "Превышен лимит операций"},
        {"success": False, "error": "Ошибка банка-эмитента"},
        {"success": False, "error": "Карта не поддерживает онлайн-платежи"},
    ]
    
    # Некоторые номера карт всегда дают определенный результат для тестирования
    test_cards = {
        '4000000000000002': {"success": False, "error": "Карта отклонена"},
        '4000000000009995': {"success": False, "error": "Недостаточно средств"},
        '4000000000009987': {"success": False, "error": "Карта потеряна"},
        '4000000000009979': {"success": False, "error": "Карта украдена"},
        '4000000000000069': {"success": False, "error": "Карта просрочена"},
        '4000000000000127': {"success": False, "error": "Неверный CVC"},
        '4000000000000119': {"success": False, "error": "Обработчик отклоняет карту"},
        '4000000000000259': {"success": False, "error": "Обработчик отклоняет карту"},
        '4000000000000267': {"success": False, "error": "Обработчик отклоняет карту"},
        '4000000000000244': {"success": False, "error": "Обработчик отклоняет карту"},
    }
    
    if clean_card_number in test_cards:
        return test_cards[clean_card_number]
    
    # 70% успешных платежей, 30% отказов
    if random.random() < 0.7:
        return {
            "success": True, 
            "transaction_id": str(uuid.uuid4())[:8].upper(),
            "amount": amount,
            "card_type": get_card_type(clean_card_number),
            "card_last4": clean_card_number[-4:]
        }
    else:
        return random.choice(failure_scenarios)

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/pay", methods=["POST"])
def pay():
    # Получаем данные из формы
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    card_number = request.form.get("card_number", "").strip()
    expiry = request.form.get("expiry", "").strip()
    cvv = request.form.get("cvv", "").strip()
    
    # Валидация на стороне сервера
    errors = []
    
    if not name or len(name) < 2:
        errors.append("Введите корректное имя")
    
    if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        errors.append("Введите корректный email")
    
    if not card_number or len(card_number.replace(' ', '')) != 16:
        errors.append("Введите корректный номер карты")
    
    if not expiry or not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', expiry):
        errors.append("Введите корректный срок действия")
    
    if not cvv or len(cvv) != 3 or not cvv.isdigit():
        errors.append("Введите корректный CVV")
    
    if errors:
        flash("Ошибки в форме: " + "; ".join(errors), "error")
        return redirect(url_for("index"))
    
    # Обрабатываем платеж
    payment_result = process_payment(card_number, expiry, cvv)
    
    # Сохраняем результат в сессии
    session['payment_result'] = payment_result
    session['customer_name'] = name
    session['customer_email'] = email
    
    if payment_result["success"]:
        return redirect(url_for("success"))
    else:
        return redirect(url_for("failure"))

@app.route("/success")
def success():
    result = session.get('payment_result')
    if not result or not result.get('success'):
        return redirect(url_for("index"))
    
    return render_template("success.html", 
                         result=result,
                         customer_name=session.get('customer_name'),
                         customer_email=session.get('customer_email'))

@app.route("/failure")
def failure():
    result = session.get('payment_result')
    if not result or result.get('success'):
        return redirect(url_for("index"))
    
    return render_template("failure.html", 
                         result=result,
                         customer_name=session.get('customer_name'),
                         customer_email=session.get('customer_email'))

@app.route("/result/<status>")
def result(status):
    # Старый маршрут для обратной совместимости
    if status == "success":
        return redirect(url_for("success"))
    else:
        return redirect(url_for("failure"))

if __name__ == "__main__":
    app.run(debug=True)
