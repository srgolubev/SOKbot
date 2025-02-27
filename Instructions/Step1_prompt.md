# Chain of Prompts for Claude Sonnet 3.5: Step1 - Integration of AI for Command Processing in Telegram Bot

This document contains a sequence of prompts to guide the development of the first stage: integrating AI to process incoming commands within a Telegram bot. Each prompt addresses a specific task, forming a sequential pipeline.

---

## Prompt 1: Basic Setup of the Telegram Bot

**Description:**  
Create a basic Python script using the `python-telegram-bot` library. The script should:
- Connect to the Telegram Bot API using an API token.
- Receive incoming messages from users.
- Respond to each message with a simple confirmation (e.g., "Сообщение получено").

**Prompt:**  
> Напиши на Python базовый скрипт, использующий библиотеку `python-telegram-bot`, который:
> - Подключается к Telegram Bot API с использованием API-токена.
> - Принимает входящие сообщения от пользователей.
> - Отвечает на каждое полученное сообщение простым подтверждением, например: "Сообщение получено".
> 
> Код должен быть структурирован, с комментариями, объясняющими ключевые части.

---

## Prompt 2: Implementation of the NLP Parser for Commands

**Description:**  
Develop a Python function that processes a command string such as:

"@бот, создай таблицу Фестиваль гто, добавь разделы аренда, судьи, звук, свет, сцена, сувенирка, наградная"

The function must use natural language processing (NLP) techniques (e.g., a transformer model from Hugging Face or spaCy with custom rules) to extract:
- The project name (e.g., "Фестиваль гто").
- A list of sections (e.g., `["аренда", "судьи", "звук", "свет", "сцена", "сувенирка", "наградная"]`).

The function should return the result in a JSON-like format.

**Prompt:**  
> Разработай функцию на Python, которая принимает строку команды, например:
> 
> ```
> "@бот, создай таблицу Фестиваль гто, добавь разделы аренда, судьи, звук, свет, сцена, сувенирка, наградная"
> ```
> 
> Функция должна с использованием технологии обработки естественного языка (NLP) извлечь:
> - Название проекта (например, "Фестиваль гто").
> - Список разделов (например, `["аренда", "судьи", "звук", "свет", "сцена", "сувенирка", "наградная"]`).
> 
> Используй современные библиотеки: можно применить модель на основе трансформеров (например, Hugging Face Transformers) или настроить spaCy с кастомными правилами/Matcher. Функция должна возвращать результат в виде JSON-объекта:
> 
> ```python
> {"project_name": "Фестиваль гто", "sections": ["аренда", "судьи", "звук", "свет", "сцена", "сувенирка", "наградная"]}
> ```
> 
> Добавь подробные комментарии по логике извлечения сущностей.

---

## Prompt 3: Integrating the NLP Parser with the Telegram Bot

**Description:**  
Combine the code from the previous steps. Upon receiving a message, the bot should:
- Call the NLP parser function to process the text.
- Use the extracted data (project name and sections) to form a reply message.

**Prompt:**  
> Объедини код из предыдущих шагов:
> - После получения сообщения ботом, вызови функцию NLP-парсера для обработки текста.
> - Полученные данные (название проекта и разделы) используй для формирования ответного сообщения, например:
> 
> ```
> "Новый проект 'Фестиваль гто' с разделами: аренда, судьи, звук, свет, сцена, сувенирка, наградная."
> ```
> 
> Обеспечь, чтобы бот корректно передавал данные из NLP-модуля и отправлял пользователю сообщение с результатом.

---

## Prompt 4: Error Handling and Logging

**Description:**  
Enhance the bot and NLP parser code by:
- Adding exception handling (`try/except`) to capture parsing and messaging errors.
- Implementing logging (using Python's `logging` module) to record all incoming messages and errors to a log file.
- Ensuring that, in case of an error, the bot sends a clear error message to the user.

**Prompt:**  
> Расширь код Telegram-бота и NLP-парсера:
> - Добавь обработку исключений (try/except) для перехвата ошибок в процессе парсинга и отправки сообщений.
> - Реализуй механизм логирования с использованием модуля `logging`, чтобы все входящие сообщения и возникающие ошибки записывались в лог-файл.
> - В случае ошибки отправляй пользователю понятное сообщение об ошибке.

---

## Prompt 5: Formatting the Result for Further Integration

**Description:**  
Ensure that the NLP parser function returns data in a structured JSON format suitable for the next module (Google Sheets integration). Document the output format with comments:
- `project_name`: a string containing the project name.
- `sections`: a list of strings, each representing a section.

**Prompt:**  
> Проверь, что функция NLP-парсера возвращает данные в структурированном формате (JSON), пригодном для дальнейшей передачи в модуль создания нового листа в Google Таблицах.
> 
> Опиши формат выходных данных в виде комментариев:
> - Ключ `project_name` – строка с названием проекта.
> - Ключ `sections` – список строк, каждая из которых соответствует разделу.
> 
> Убедись, что результат выглядит следующим образом:
> 
> ```python
> {"project_name": "Фестиваль гто", "sections": ["аренда", "судьи", "звук", "свет", "сцена", "сувенирка", "наградная"]}
> ```

---

# Summary

Эта последовательная цепочка промптов поможет разработать:
1. Основной функционал Telegram-бота.
2. Модуль обработки естественного языка для извлечения ключевых данных из команд.
3. Интеграцию NLP-модуля с ботом.
4. Механизмы обработки ошибок и логирования.
5. Подготовку структурированных данных для дальнейшей автоматизации (например, интеграции с Google Sheets).

Сохраните этот файл и используйте его в качестве руководства для реализации первого этапа проекта в Claude Sonnet 3.5.

 
 Всё выглядит как в шаблоне. Отлично!

Теперь приведем решение к тому что нужно нам:
Функция получаетна вход объект вида: {"project_name": "Фестиваль гто", "sections": ["аренда", "судьи", "звук", "свет", "сцена", "сувенирка", "наградная"]}

Берет Идентификатор таблицы из файла @client_secrets.json переменная "main_sheet". В эту таблицу функция добавляет лист с содержимым переменной "project_name". Первые три строки листа заполняются первыми тремя строками таблицы переменной "template_top". После этого для каждой строки из списка переменной "sections" функция добавляет строки из таблицы переменной "template_sections" заменяя {sectionName} на содержимое переменной "section".