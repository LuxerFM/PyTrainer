"""Місяці 3–4 — інструменти й перші проєкти: інтернет, парсинг, алгоритми."""

from .schema import Month, stub, topic

MONTH = Month(
    title="Місяці 3–4 · Інструменти + перші проєкти",
    subtitle="Перші роботи в портфоліо",
    topics=(
        topic(
            "Дані з інтернету",
            stub("m3-requests", "requests: перший запит до API"),
            stub("m3-json-api", "Розбір JSON-відповіді"),
            stub("m3-parser", "BeautifulSoup: парсер сайту"),
            stub("m3-csv", "Проєкт: парсер цін → CSV"),
            stub("m3-nbu", "Проєкт: курси НБУ у своїй програмі"),
        ),
        topic(
            "Алгоритми й типи (міні-блок, 2 тижні)",
            stub("m3-algo", "Сортування, пошук, складність на пальцях"),
            stub("m3-algo-practice", "10 задач на списки й словники"),
            stub("m3-typing", "Анотації типів у своєму коді"),
        ),
        topic(
            "Робота з кодом як у команді",
            stub("m3-git-branch", "Гілки та merge у Git"),
            stub("m3-github", "Перший проєкт на GitHub з гарним README"),
            stub("m3-docs", "Читання офіційної документації"),
        ),
    ),
)
