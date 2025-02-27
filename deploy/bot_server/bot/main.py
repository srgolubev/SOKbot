import os
import json
import logging
import pytz
from typing import Dict, Any
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
from gpt_command_parser import GPTCommandParser, ParsingError

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаем обработчик для записи в файл
file_handler = logging.FileHandler('telegram_bot.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Создаем форматтер
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(file_handler)

# Словарь для хранения контекста пользователей
user_context: Dict[int, Dict[str, Any]] = {}

def log_user_action(user_id: int, username: str, action: str):
    """Логирует действие пользователя"""
    logger.info(f"User {user_id} (@{username}): {action}")

def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    if not update.effective_user:
        return
        
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    log_user_action(user_id, username, "Запустил бота командой /start")
    
    welcome_message = (
        "👋 Привет! Я бот для создания проектных таблиц.\n\n"
        "Просто напиши мне название проекта и его разделы, например:\n"
        "\"Создай проект Фестиваль ГТО с разделами аренда, судьи и звук\"\n\n"
        "Я пойму твою команду и помогу создать нужную таблицу! 📊"
    )
    update.message.reply_text(welcome_message)

def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    if not update.effective_user:
        return
        
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    log_user_action(user_id, username, "Запросил помощь командой /help")
    
    help_text = (
        "🤖 Вот что я умею:\n\n"
        "1️⃣ Создавать проектные таблицы из ваших сообщений\n"
        "2️⃣ Понимать команды на естественном языке\n"
        "3️⃣ Работать с разными разделами проекта\n\n"
        "Примеры команд:\n"
        "• \"Создай проект День города с разделами сцена, звук и свет\"\n"
        "• \"Нужна таблица для проекта Марафон, разделы: награждение, реклама\"\n"
        "• \"Сделай таблицу Фестиваль красок с волонтерами и фотографами\"\n\n"
        "Просто напиши мне, что нужно сделать! 😊"
    )
    update.message.reply_text(help_text)

def handle_message(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений"""
    if not update.message or not update.effective_user:
        return
        
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    message_text = update.message.text
    
    log_user_action(user_id, username, f"Отправил сообщение: {message_text}")
    
    try:
        # Создаем парсер при первом использовании
        if 'parser' not in context.bot_data:
            context.bot_data['parser'] = GPTCommandParser()
        
        # Парсим команду
        result = context.bot_data['parser'].parse_command(message_text)
        
        if result["is_create_table_command"]:
            if result["project_name"] and result["sections"]:
                # Сохраняем контекст пользователя
                user_context[user_id] = {
                    "project_name": result["project_name"],
                    "sections": result["sections"],
                    "awaiting_confirmation": True
                }
                
                confirmation_message = (
                    f"📋 Я понял, что вы хотите создать проект:\n\n"
                    f"📌 Название: {result['project_name']}\n"
                    f"📑 Разделы:\n" + 
                    "\n".join(f"   • {section}" for section in result['sections']) +
                    "\n\nВсё верно? Ответьте 'да' или 'нет'"
                )
                update.message.reply_text(confirmation_message)
                log_user_action(user_id, username, "Запрошено подтверждение создания проекта")
                
            else:
                error_message = "❌ Извините, я не смог определить название проекта или разделы из вашего сообщения.\n\nПопробуйте написать более конкретно, например:\n\"Создай проект День города с разделами сцена, звук и свет\""
                update.message.reply_text(error_message)
                log_user_action(user_id, username, "Не удалось определить параметры проекта")
                
        elif user_id in user_context and user_context[user_id].get("awaiting_confirmation"):
            # Обработка ответа на подтверждение
            if message_text.lower() in ["да", "yes", "конечно", "верно"]:
                project_data = user_context[user_id]
                # TODO: Здесь будет создание таблицы
                success_message = (
                    f"✅ Отлично! Я создал проект \"{project_data['project_name']}\" "
                    f"со следующими разделами:\n" +
                    "\n".join(f"   • {section}" for section in project_data['sections'])
                )
                update.message.reply_text(success_message)
                log_user_action(user_id, username, f"Подтвердил создание проекта {project_data['project_name']}")
                del user_context[user_id]
                
            elif message_text.lower() in ["нет", "no", "неверно", "неправильно"]:
                update.message.reply_text("🔄 Хорошо, давайте попробуем снова. Опишите проект заново.")
                log_user_action(user_id, username, "Отклонил создание проекта")
                del user_context[user_id]
                
        else:
            # Если это не команда создания таблицы и нет ожидания подтверждения
            update.message.reply_text("🤔 Извините, я не совсем понял, что нужно сделать. Попробуйте описать задачу подробнее или используйте /help для справки.")
            log_user_action(user_id, username, "Отправил неопознанную команду")
            
    except ParsingError as e:
        error_message = f"❌ Произошла ошибка при обработке команды: {str(e)}\n\nПопробуйте переформулировать запрос или используйте /help для справки."
        update.message.reply_text(error_message)
        logger.error(f"Ошибка парсинга для пользователя {user_id}: {str(e)}")
        
    except Exception as e:
        error_message = "❌ Произошла непредвиденная ошибка. Попробуйте позже или обратитесь к администратору."
        update.message.reply_text(error_message)
        logger.error(f"Критическая ошибка для пользователя {user_id}: {str(e)}")

def error_handler(update: Update, context: CallbackContext):
    """Глобальный обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    if update.effective_message:
        update.effective_message.reply_text(
            "😔 Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
        )

def main():
    """Основная функция запуска бота"""
    try:
        # Загружаем переменные окружения
        load_dotenv()
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
            
        # Создаем Updater
        updater = Updater(token)
        
        # Получаем диспетчер
        dispatcher = updater.dispatcher
        
        # Добавляем обработчики
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        # Добавляем глобальный обработчик ошибок
        dispatcher.add_error_handler(error_handler)
        
        # Запускаем бота
        logger.info("Бот запущен")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {str(e)}")
        raise

if __name__ == "__main__":
    main()
