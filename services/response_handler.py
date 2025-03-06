from flask import jsonify

# Общий обработчик ошибок
def default_response(data, status_code):
    # Возвращаем сообщение об ошибке с правильным статусом
    return jsonify( data ), status_code
