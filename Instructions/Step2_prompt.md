# Chain of Prompts for Claude Sonnet 3.5: Step 3 - Integration with Google Sheets API

This document contains a sequence of prompts designed to guide Claude Sonnet 3.5 in generating Python code for integrating with the Google Sheets API. The stage includes setting up authentication, creating a new sheet using a template, writing a list of section headers, and testing the integration.

---

## Prompt 1: Google OAuth Setup and Authentication

**Objective:**  
Generate Python code that handles authentication with the Google Sheets API using OAuth 2.0. The code should:
- Load OAuth credentials from a file (e.g., `credentials.json`).
- Use libraries such as `google-auth` and `google-auth-oauthlib` to perform the authentication.
- Create and return a service object for interacting with the Google Sheets API.

**Prompt:**  
> Напиши на Python код, который выполняет аутентификацию с Google Sheets API с использованием OAuth 2.0. Код должен:
> - Загружать учетные данные из файла (например, `credentials.json`).
> - Использовать библиотеки `google-auth` и `google-auth-oauthlib` для выполнения аутентификации.
> - Создавать и возвращать объект сервиса для взаимодействия с Google Sheets API.
> 
> Добавь подробные комментарии к коду, объясняющие шаги аутентификации.

---

## Prompt 2: Function to Create a New Sheet by Template

**Objective:**  
Generate a Python function that creates a new sheet in an existing Google Spreadsheet using a predefined template. The function should:
- Accept the spreadsheet ID and the name of the new sheet.
- Use the Google Sheets API method `batchUpdate` to add a new sheet.
- Optionally apply basic formatting to match the template.

**Prompt:**  
> Напиши на Python функцию `create_new_sheet(service, spreadsheet_id, sheet_name)`, которая:
> - Принимает объект `service` для Google Sheets API, идентификатор таблицы и имя нового листа.
> - Создает новый лист в указанной таблице, используя метод `batchUpdate`.
> - При необходимости применяет базовое форматирование для нового листа, основываясь на заранее заданном шаблоне.
> 
> Добавь подробные комментарии, описывающие каждый шаг функции.

---

## Prompt 3: Function to Write List of Sections as Headers

**Objective:**  
Generate a Python function that writes a list of section names as headers in the newly created sheet. The function should:
- Accept the spreadsheet ID, sheet name (or sheet ID), and a list of sections.
- Use the Google Sheets API method `values.update` or `values.append` to write data into the first row of the sheet.

**Prompt:**  
> Напиши на Python функцию `write_section_headers(service, spreadsheet_id, sheet_name, sections)`, которая:
> - Принимает объект `service`, идентификатор таблицы, имя нового листа и список разделов (например, `["аренда", "судьи", "звук", "свет", "сцена", "сувенирка", "наградная"]`).
> - Записывает этот список как заголовки в первую строку указанного листа, используя метод `values.update` или `values.append`.
> 
> Добавь подробные комментарии, описывающие логику записи данных.

---

## Prompt 4: Testing the Google Sheets Integration

**Objective:**  
Generate a Python script that tests the integration by:
- Authenticating and obtaining the `service` object.
- Creating a new sheet in a test Google Spreadsheet.
- Writing a sample list of section headers to the new sheet.
- Printing the results of each operation to the console.

**Prompt:**  
> Напиши на Python скрипт, который:
> - Выполняет аутентификацию с Google Sheets API и получает объект `service` (используя код из Prompt 1).
> - Вызывает функцию `create_new_sheet`, чтобы создать новый лист в тестовой Google Таблице.
> - Вызывает функцию `write_section_headers` для записи списка разделов в созданный лист.
> - Выводит в консоль результаты выполнения каждой операции (например, успешное создание листа, успешное обновление данных).
> 
> Добавь подробные комментарии, описывающие тестовые шаги.

---

# Summary

Эта последовательная цепочка промптов предназначена для разработки функций интеграции с Google Sheets API, включая аутентификацию, создание нового листа по шаблону и запись данных. Используйте данные промпты в Claude Sonnet 3.5 для генерации соответствующего кода на Python для этапа 3 проекта.
