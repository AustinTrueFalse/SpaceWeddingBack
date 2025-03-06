from flask import jsonify

# Общий обработчик ошибок
def default_error_response(message, status_code):
    # Возвращаем сообщение об ошибке с правильным статусом
    return jsonify({"error": { 
        "message": message,
        "souce": "server"
        }
    }), status_code

# Обработчик ошибок валидации
def validation_error_response(message, status_code):
    # Возвращаем ошибку валидации с соответствующим статусом
    return jsonify({"error": { 
        "message": message,
        "souce": "server"
        }
    }), status_code

def firebase_error_response(message, status_code):
    # Возвращаем ошибку валидации с соответствующим статусом
    return jsonify({"error": { 
        "message": message,
        "souce": "firebase"
        }
    }), status_code
