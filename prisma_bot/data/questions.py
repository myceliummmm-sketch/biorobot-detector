"""
Questions structure for IDEA phase cards.
Each card has questions with A/B/C/D options to reduce friction.
Based on Prisma Character File v4.3
"""

from typing import Dict, List, Optional

# Card types in order for IDEA phase
IDEA_CARDS_ORDER = ["product", "problem", "audience", "value", "vision"]

# Questions for each card type with A/B/C/D options
IDEA_QUESTIONS: Dict[str, Dict] = {
    "product": {
        "title": "Продукт",
        "emoji": "🎯",
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


def format_question_message(card_type: str, question_number: int) -> Optional[str]:
    """Format a question for sending to user with A/B/C/D options"""
    card = get_card_questions(card_type)
    question = get_question(card_type, question_number)

    if not card or not question:
        return None

    # Build message
    header = f"{card['emoji']} *{card['title']}* ({question_number}/5)"

    # First question includes card intro
    if question_number == 1:
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
