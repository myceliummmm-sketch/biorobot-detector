"""
Questions structure for IDEA phase cards.
Each card has questions with A/B/C/D options to reduce friction.
Based on Prisma Character File v4.3 and IDEA_PHASE_FLOW v2.7

Characters per card:
- V-01 Product: 🌲 Ever Green + 💎 Prisma
- V-02 Problem: ☢️ Toxic + 💎 Prisma
- V-03 Audience: 🔥 Phoenix + 💎 Prisma
- V-04 Value: 🌲 Ever Green + 💎 Prisma
- V-05 Vision: 🎨 Virgil + 💎 Prisma
"""

from typing import Dict, List, Optional
import random

# Card types in order for IDEA phase
IDEA_CARDS_ORDER = ["product", "problem", "audience", "value", "vision"]

# Character-specific intros for each card
CARD_CHARACTER_INTROS = {
    "product": {
        "lead": "🌲 Ever",
        "intro": "🌲 *Ever Green:* Карточка 01: Idea Seed. Зерно идеи.\n\nЗнаешь, самые великие компании начинались с одного предложения.\nAirbnb: «Сдавай свою комнату путешественникам». Uber: «Нажми кнопку — приедет машина».\n\n💎 *Prisma:* Твоя очередь! Не думай долго — скажи как есть. Отшлифуем вместе.",
    },
    "problem": {
        "lead": "☢️ Toxic",
        "intro": "☢️ *Toxic:* Привет. Давай без реверансов.\n\n«Не знают с чего начать» — это не боль. Это дискомфорт.\nБоль — когда уже попробовал и обжёгся. Потерял деньги. Запустил продукт в пустоту.\n\n💎 *Prisma:* Копнём глубже. Какую конкретную боль решает твой продукт?",
    },
    "audience": {
        "lead": "🔥 Phoenix",
        "intro": "🔥 *Phoenix:* Привет! Люблю эту часть.\n\nЗабудь «целевая аудитория 25-34». Это для отчётов.\nМне нужен *один человек*.\n\nПредставь: кофейня. За соседним столиком — твой идеальный клиент.\n\n💎 *Prisma:* Как выглядит? Что в руках? О чём думает?",
    },
    "value": {
        "lead": "🌲 Ever",
        "intro": "🌲 *Ever Green:* Время для самого важного — ценность.\n\nЕсли через 3 месяца скажешь «получилось!» — какие цифры увидишь?\n\n💎 *Prisma:* Давай честно. Что конкретно получит пользователь?",
    },
    "vision": {
        "lead": "🎨 Virgil",
        "intro": "🎨 *Virgil:* Привет. Моя любимая часть — охота за странностью.\n\nЗабудь «лучше» и «больше функций». Скучно. Копируемо.\nИщу *странность*. То, что делает тебя — тебя.\n\n💎 *Prisma:* Последняя карточка! Самая важная. Почему выберут именно тебя?",
    },
}

# Team voting comments for card completion
TEAM_VOTING = {
    "product": {
        "high": [
            {"char": "🌲 Ever", "score": "8/10", "comment": "Сильная аналогия, понятный рынок"},
            {"char": "🔥 Phoenix", "score": "7/10", "comment": "Хороший маркетинговый ход"},
            {"char": "☢️ Toxic", "score": "6/10", "comment": "Посмотрим. Пока это просто слова"},
        ],
        "medium": [
            {"char": "🌲 Ever", "score": "6/10", "comment": "Идея понятна, но нужна уникальность"},
            {"char": "🔥 Phoenix", "score": "5/10", "comment": "Можно работать, но нужно отточить"},
            {"char": "☢️ Toxic", "score": "5/10", "comment": "Пока слабо. Копнём глубже"},
        ],
    },
    "problem": {
        "high": [
            {"char": "☢️ Toxic", "score": "8/10", "comment": "Боль реальная. Копнул глубоко"},
            {"char": "🌲 Ever", "score": "8/10", "comment": "Сильная формулировка. Продаётся"},
            {"char": "🔥 Phoenix", "score": "7/10", "comment": "Понятно кому продавать"},
        ],
        "medium": [
            {"char": "☢️ Toxic", "score": "6/10", "comment": "Боль есть, но размытая"},
            {"char": "🌲 Ever", "score": "5/10", "comment": "Нужно конкретнее"},
            {"char": "🔥 Phoenix", "score": "5/10", "comment": "Пока не цепляет"},
        ],
    },
    "audience": {
        "high": [
            {"char": "🔥 Phoenix", "score": "9/10", "comment": "Живой человек, не статистика!"},
            {"char": "🌲 Ever", "score": "8/10", "comment": "Знаем для кого строим"},
            {"char": "☢️ Toxic", "score": "7/10", "comment": "Проверим, существует ли он"},
        ],
        "medium": [
            {"char": "🔥 Phoenix", "score": "6/10", "comment": "Персона есть, но абстрактная"},
            {"char": "🌲 Ever", "score": "5/10", "comment": "Нужно больше деталей"},
            {"char": "☢️ Toxic", "score": "5/10", "comment": "Слишком generic"},
        ],
    },
    "value": {
        "high": [
            {"char": "🌲 Ever", "score": "8/10", "comment": "Реалистичные цели"},
            {"char": "☢️ Toxic", "score": "7/10", "comment": "Посмотрим через 90 дней"},
            {"char": "🔥 Phoenix", "score": "7/10", "comment": "Понятная воронка"},
        ],
        "medium": [
            {"char": "🌲 Ever", "score": "5/10", "comment": "Метрики размытые"},
            {"char": "☢️ Toxic", "score": "5/10", "comment": "Как измерить-то?"},
            {"char": "🔥 Phoenix", "score": "5/10", "comment": "Нужна конкретика"},
        ],
    },
    "vision": {
        "high": [
            {"char": "🎨 Virgil", "score": "9/10", "comment": "Это история, которую хочется рассказать"},
            {"char": "🌲 Ever", "score": "9/10", "comment": "Сильное позиционирование"},
            {"char": "🔥 Phoenix", "score": "9/10", "comment": "Продаваемая уникальность"},
            {"char": "☢️ Toxic", "score": "8/10", "comment": "Посмотрим, купят ли"},
        ],
        "medium": [
            {"char": "🎨 Virgil", "score": "6/10", "comment": "Идея есть, но не цепляет"},
            {"char": "🌲 Ever", "score": "5/10", "comment": "Нужна уникальность"},
            {"char": "🔥 Phoenix", "score": "5/10", "comment": "Пока не вижу историю"},
        ],
    },
}


def get_team_voting(card_type: str, quality: str = "medium") -> str:
    """Generate team voting comments for card completion"""
    voting = TEAM_VOTING.get(card_type, {}).get(quality, [])
    if not voting:
        return ""

    lines = ["*Голосование команды:*\n"]
    total_score = 0

    for vote in voting:
        lines.append(f"{vote['char']}: {vote['score']} — «{vote['comment']}»")
        score_num = int(vote['score'].split('/')[0])
        total_score += score_num

    avg_score = total_score / len(voting) if voting else 0

    # Determine rarity
    if avg_score >= 8.5:
        rarity = "🌟 LEGENDARY"
    elif avg_score >= 7.5:
        rarity = "💎 EPIC"
    elif avg_score >= 6:
        rarity = "✨ RARE"
    else:
        rarity = "💚 COMMON"

    lines.append(f"\n*Итого: {avg_score:.1f}/10 — {rarity}*")

    return "\n".join(lines)


def get_card_intro(card_type: str) -> str:
    """Get character-specific intro for a card"""
    card_data = CARD_CHARACTER_INTROS.get(card_type, {})
    return card_data.get("intro", "")


# Questions for each card type with A/B/C/D options
IDEA_QUESTIONS: Dict[str, Dict] = {
    "product": {
        "title": "Продукт",
        "emoji": "🎯",
        "lead_char": "🌲 Ever",
        "intro": "Начнём с главного. Что ты создаёшь?",
        "questions": [
            {
                "id": 1,
                "text": "Что именно ты строишь?",
                "field": "product_type",
                "options": [
                    {"key": "A", "text": "Мобильное приложение"},
                    {"key": "B", "text": "Веб-сервис"},
                    {"key": "C", "text": "Telegram-бот"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 2,
                "text": "Для кого это?",
                "field": "target_scope",
                "options": [
                    {"key": "A", "text": "Для себя (пет-проект)"},
                    {"key": "B", "text": "Для узкой ниши"},
                    {"key": "C", "text": "Для широкой аудитории"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 3,
                "text": "Опиши продукт одним предложением",
                "field": "description",
                "options": None,  # Open question
                "hint": "Если бы друг спросил 'что ты делаешь?' — как ответишь за 10 секунд?"
            },
            {
                "id": 4,
                "text": "Какую главную функцию выполняет продукт?",
                "field": "core_function",
                "options": None,
                "hint": "Одно ключевое действие, которое делает пользователь"
            },
            {
                "id": 5,
                "text": "Какой минимальный MVP можно запустить за 2 недели?",
                "field": "mvp",
                "options": None,
                "hint": "Самая простая версия, которая уже решает проблему"
            }
        ]
    },

    "problem": {
        "title": "Проблема",
        "emoji": "🔥",
        "lead_char": "☢️ Toxic",
        "intro": "Теперь про боль. Какую проблему ты решаешь?",
        "questions": [
            {
                "id": 1,
                "text": "Какую проблему ты решаешь?",
                "field": "problem_type",
                "options": [
                    {"key": "A", "text": "Экономия времени"},
                    {"key": "B", "text": "Экономия денег"},
                    {"key": "C", "text": "Упрощение сложного процесса"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 2,
                "text": "Кто конкретно от этого страдает?",
                "field": "who_suffers",
                "options": [
                    {"key": "A", "text": "Студенты / молодёжь"},
                    {"key": "B", "text": "Профессионалы / специалисты"},
                    {"key": "C", "text": "Предприниматели / бизнес"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 3,
                "text": "Как они справляются сейчас?",
                "field": "current_solutions",
                "options": [
                    {"key": "A", "text": "Никак, терпят"},
                    {"key": "B", "text": "Костыли / Excel"},
                    {"key": "C", "text": "Конкуренты"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 4,
                "text": "Насколько эта боль острая?",
                "field": "pain_level",
                "options": [
                    {"key": "A", "text": "Критичная — не могут работать"},
                    {"key": "B", "text": "Важная — мешает, но терпят"},
                    {"key": "C", "text": "Nice-to-have — было бы неплохо"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 5,
                "text": "Сколько готовы платить за решение?",
                "field": "willingness_to_pay",
                "options": [
                    {"key": "A", "text": "Бесплатно / freemium"},
                    {"key": "B", "text": "$5-20 / месяц"},
                    {"key": "C", "text": "$50+ / месяц"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            }
        ]
    },

    "audience": {
        "title": "Аудитория",
        "emoji": "👥",
        "lead_char": "🔥 Phoenix",
        "intro": "Давай познакомимся с твоим пользователем.",
        "questions": [
            {
                "id": 1,
                "text": "Как зовут твоего идеального пользователя?",
                "field": "persona_name",
                "options": None,
                "hint": "Дай ему имя — так легче думать о реальном человеке"
            },
            {
                "id": 2,
                "text": "Сколько ему лет?",
                "field": "age_group",
                "options": [
                    {"key": "A", "text": "18-25"},
                    {"key": "B", "text": "25-35"},
                    {"key": "C", "text": "35-45"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 3,
                "text": "Чем занимается?",
                "field": "occupation",
                "options": [
                    {"key": "A", "text": "Работает в найме"},
                    {"key": "B", "text": "Фрилансер"},
                    {"key": "C", "text": "Предприниматель"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 4,
                "text": "Где проводит время онлайн?",
                "field": "channels",
                "options": [
                    {"key": "A", "text": "Telegram / Discord"},
                    {"key": "B", "text": "Instagram / TikTok"},
                    {"key": "C", "text": "LinkedIn / Twitter"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 5,
                "text": "О чём он думает перед сном?",
                "field": "worries",
                "options": None,
                "hint": "Что его тревожит? Это про эмпатию — попробуй почувствовать"
            }
        ]
    },

    "value": {
        "title": "Ценность",
        "emoji": "💎",
        "lead_char": "🌲 Ever",
        "intro": "В чём ценность? Почему выберут именно тебя?",
        "questions": [
            {
                "id": 1,
                "text": "Какой главный результат получает пользователь?",
                "field": "main_outcome",
                "options": [
                    {"key": "A", "text": "Экономит время"},
                    {"key": "B", "text": "Зарабатывает больше"},
                    {"key": "C", "text": "Получает новый навык"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 2,
                "text": "За какое время увидит первый результат?",
                "field": "time_to_value",
                "options": [
                    {"key": "A", "text": "Мгновенно"},
                    {"key": "B", "text": "За день"},
                    {"key": "C", "text": "За неделю"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 3,
                "text": "Что измеримо улучшится?",
                "field": "success_metric",
                "options": None,
                "hint": "Конкретная метрика: часы, деньги, количество"
            },
            {
                "id": 4,
                "text": "Почему выберут тебя, а не конкурента?",
                "field": "competitive_advantage",
                "options": [
                    {"key": "A", "text": "Дешевле"},
                    {"key": "B", "text": "Проще"},
                    {"key": "C", "text": "Уникальная фича"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 5,
                "text": "Какую эмоцию испытает после использования?",
                "field": "emotional_outcome",
                "options": [
                    {"key": "A", "text": "Облегчение"},
                    {"key": "B", "text": "Гордость"},
                    {"key": "C", "text": "Уверенность"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            }
        ]
    },

    "vision": {
        "title": "Видение",
        "emoji": "🔮",
        "lead_char": "🎨 Virgil",
        "intro": "Куда всё это ведёт? Какая большая картина?",
        "questions": [
            {
                "id": 1,
                "text": "Как выглядит успех через 1 год?",
                "field": "year_one",
                "options": [
                    {"key": "A", "text": "100+ платящих пользователей"},
                    {"key": "B", "text": "1000+ активных пользователей"},
                    {"key": "C", "text": "Выход на прибыль"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 2,
                "text": "Какой рынок хочешь захватить?",
                "field": "target_market",
                "options": [
                    {"key": "A", "text": "Локальный / один город"},
                    {"key": "B", "text": "Страна / регион"},
                    {"key": "C", "text": "Глобальный"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 3,
                "text": "Что изменится в мире, если добьёшься успеха?",
                "field": "impact",
                "options": None,
                "hint": "Подумай масштабно — как это повлияет на людей?"
            },
            {
                "id": 4,
                "text": "Какой следующий milestone после MVP?",
                "field": "next_milestone",
                "options": [
                    {"key": "A", "text": "Первые 10 платящих"},
                    {"key": "B", "text": "Product-market fit"},
                    {"key": "C", "text": "Привлечение инвестиций"},
                    {"key": "D", "text": "Свой вариант"}
                ]
            },
            {
                "id": 5,
                "text": "Почему именно ты должен это построить?",
                "field": "why_you",
                "options": None,
                "hint": "Твой unfair advantage: опыт, связи, инсайты"
            }
        ]
    }
}


def get_card_questions(card_type: str) -> Optional[Dict]:
    """Get questions for a specific card type"""
    return IDEA_QUESTIONS.get(card_type.lower())


def get_question(card_type: str, question_number: int) -> Optional[Dict]:
    """Get specific question from a card"""
    card = get_card_questions(card_type)
    if not card:
        return None
    questions = card.get("questions", [])
    if 1 <= question_number <= len(questions):
        return questions[question_number - 1]
    return None


def get_next_card(current_card: str) -> Optional[str]:
    """Get next card in the IDEA flow"""
    try:
        current_index = IDEA_CARDS_ORDER.index(current_card.lower())
        if current_index < len(IDEA_CARDS_ORDER) - 1:
            return IDEA_CARDS_ORDER[current_index + 1]
    except ValueError:
        pass
    return None


def format_question_message(card_type: str, question_number: int, use_character_intro: bool = True) -> Optional[str]:
    """Format a question for sending to user with A/B/C/D options"""
    card = get_card_questions(card_type)
    question = get_question(card_type, question_number)

    if not card or not question:
        return None

    # Build message
    header = f"{card['emoji']} *{card['title']}* ({question_number}/5)"

    # First question includes character-specific intro
    if question_number == 1 and use_character_intro:
        char_intro = get_card_intro(card_type)
        if char_intro:
            text = f"{header}\n\n{char_intro}\n\n*Вопрос {question_number}:* {question['text']}"
        else:
            text = f"{header}\n\n{card['intro']}\n\n*Вопрос {question_number}:* {question['text']}"
    else:
        text = f"{header}\n\n*Вопрос {question_number}:* {question['text']}"

    # Add options if present
    options = question.get("options")
    if options:
        text += "\n"
        for opt in options:
            text += f"\n{opt['key']}) {opt['text']}"
    elif question.get("hint"):
        text += f"\n\n💡 _{question['hint']}_"

    return text


def parse_option_answer(answer: str, question: Dict) -> str:
    """Parse user's answer - handle A/B/C/D selection or custom text"""
    options = question.get("options")
    if not options:
        return answer.strip()

    answer_upper = answer.strip().upper()

    # Check if it's a letter option
    for opt in options:
        if answer_upper == opt["key"] or answer_upper.startswith(opt["key"] + ")"):
            if opt["key"] == "D":  # Custom option
                return None  # Signal to ask for custom input
            return opt["text"]

    # If not a letter, treat as custom answer
    return answer.strip()


def get_card_summary(card_type: str, answers: Dict) -> str:
    """Generate summary of completed card"""
    card = get_card_questions(card_type)
    if not card:
        return ""

    lines = [f"🎴 *{card['title']}* — завершена!\n"]

    for q in card["questions"]:
        field = q["field"]
        answer = answers.get(field, "—")
        lines.append(f"▸ {q['text'][:30]}... → {answer[:50]}")

    return "\n".join(lines)


def get_card_completion_message(card_type: str, answers: Dict, quality: str = "medium") -> str:
    """
    Generate full card completion message with team voting.

    Args:
        card_type: Type of card (product, problem, etc.)
        answers: User's answers
        quality: 'high' or 'medium' for voting comments

    Returns:
        Formatted completion message with team voting
    """
    card = get_card_questions(card_type)
    if not card:
        return "Карточка готова!"

    # Card summary
    lines = [f"{card['emoji']} *Карточка {card['title']} готова!*\n"]

    for q in card["questions"]:
        field = q["field"]
        answer = answers.get(field, "—")
        if len(answer) > 60:
            answer = answer[:60] + "..."
        lines.append(f"▸ _{answer}_")

    lines.append("")

    # Team voting
    voting = get_team_voting(card_type, quality)
    if voting:
        lines.append(voting)

    return "\n".join(lines)
