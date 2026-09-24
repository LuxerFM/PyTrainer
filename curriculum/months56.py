"""Місяці 5–6 — спеціалізація під гроші: боти, автоматизація, AI-інтеграції."""

from .schema import Month, stub, topic

MONTH = Month(
    title="Місяці 5–6 · Спеціалізація під гроші",
    subtitle="Обираємо один напрям і робимо в ньому проєкт",
    topics=(
        topic(
            "Спільне для всіх напрямів",
            stub("m5-async", "async / await: чому боти працюють асинхронно"),
            stub("m5-errors", "Логування й обробка помилок у реальній програмі"),
            stub("m5-deploy", "Деплой на Railway або VPS"),
        ),
        topic(
            "Варіант А · Telegram-боти (найшвидші гроші)",
            stub("m5-bot-basic", "aiogram: бот, що відповідає"),
            stub("m5-bot-menu", "Кнопки, меню, стани"),
            stub("m5-bot-project", "Проєкт: бот для бізнесу (запис або замовлення)"),
        ),
        topic(
            "Варіант Б · Парсинг та автоматизація",
            stub("m5-selenium", "Selenium для сайтів із JavaScript"),
            stub("m5-excel", "openpyxl і pandas: звіти замість ручної роботи"),
            stub("m5-automation-project", "Проєкт: автоматизація реальної рутини"),
        ),
        topic(
            "Варіант В · AI-інтеграції (найгарячіше)",
            stub("m5-ai-api", "OpenAI API: перший запит"),
            stub("m5-ai-prompt", "Промптинг і обробка відповідей"),
            stub("m5-ai-stream", "Стрімінг відповідей"),
            stub("m5-ai-project", "Проєкт: бот або скрипт з AI всередині"),
        ),
    ),
)
