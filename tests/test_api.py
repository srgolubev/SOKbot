import requests
import json
import logging
from typing import Dict, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def send_webhook_request(message: str, base_url: str = "http://localhost:8000") -> Optional[Dict]:
    """
    Отправляет POST-запрос на webhook endpoint.
    
    Args:
        message: Текст сообщения для обработки
        base_url: Базовый URL API (по умолчанию: http://localhost:8000)
        
    Returns:
        Optional[Dict]: Ответ сервера в виде словаря или None в случае ошибки
    """
    try:
        # Формируем URL для запроса
        url = f"{base_url}/webhook"
        
        # Подготавливаем данные запроса
        payload = {
            "message": message
        }
        
        # Задаем заголовки
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"Отправка запроса на {url}")
        logger.info(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
        
        # Отправляем POST-запрос
        response = requests.post(
            url,
            json=payload,
            headers=headers
        )
        
        # Проверяем статус ответа
        response.raise_for_status()
        
        # Получаем данные ответа
        response_data = response.json()
        logger.info(f"Получен ответ: {json.dumps(response_data, ensure_ascii=False)}")
        
        return response_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке запроса: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при разборе JSON-ответа: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        return None

def main():
    """
    Основная функция для тестирования API
    """
    # Тестовое сообщение
    test_message = "создай таблицу Фестиваль Меда, добавь разделы судьи, сувенирка, наградная"
    
    # Отправляем запрос
    result = send_webhook_request(test_message)
    
    # Проверяем результат
    if result:
        if result.get("status") == "success":
            print("\n✅ Запрос успешно обработан!")
            print(f"📝 Ответ сервера: {result['message']}\n")
        else:
            print("\n❌ Ошибка при обработке запроса!")
            print(f"🔍 Детали: {result.get('message', 'Нет деталей')}\n")
    else:
        print("\n❌ Не удалось получить ответ от сервера\n")

if __name__ == "__main__":
    main()
