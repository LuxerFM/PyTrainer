"""Місяці 7–9 — портфоліо, перший відгук і перші гроші."""

from .schema import Month, stub, topic

MONTH = Month(
    title="Місяці 7–9 · Портфоліо + перші гроші",
    subtitle="Вихід на ринок фрілансу",
    topics=(
        topic(
            "Портфоліо",
            stub("m7-portfolio", "3 проєкти з README, скріншотами й інструкцією запуску"),
            stub("m7-cv", "Резюме й профіль на GitHub"),
        ),
        topic(
            "Перший зворотний зв'язок (безкоштовно)",
            stub("m7-feedback", "Зробити 1–2 проєкти безкоштовно заради відгуку"),
            stub("m7-opensource", "Перший pull request в open source"),
        ),
        topic(
            "Перші замовлення",
            stub("m8-profiles", "Профілі на Freelancehunt, Upwork, Fiverr"),
            stub("m8-first-order", "Перше платне замовлення (навіть за $30)"),
            stub("m8-client", "Спілкування з клієнтом: оцінка, дедлайн, здача"),
        ),
        topic(
            "Зростання ціни",
            stub("m9-prices", "Підняти ціни: ціль $300–800 на місяць"),
            stub("m9-niche", "Звузити нішу й стати в ній помітним"),
            stub("m9-repeat", "Повторні клієнти й рекомендації"),
        ),
    ),
)
