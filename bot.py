import os
from dotenv import load_dotenv
import telebot
from telebot import types

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    first = message.from_user.first_name or ''
    list = message.from_user.last_name or ''
    full_name = f"{first} {list}".strip()

    bot.send_message(
        message.chat.id,
        f"Привіт! {full_name}!\n"
        f"Я — твій консультант з одягу та доставки.\n"
        "Допоможу вибрати круті речі, знайти свій розмір і швидко організувати доставку.\n"
        "Якщо маєш питання — пиши /feedback, завжди поруч! 😊\n"
        "Також можеш подивитися, що я можу зробити для тебе /catalog"
    )

# Команда /help
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "<b>Ось що я можу зробити для тебе:</b>\n"
        "✵✵✵\n"
        "/catalog — Показати наші товари\n"
        "/sizes — Допомогти вибрати розмір\n"
        "/delivery — Розповісти про доставку і оплату\n"
        "/faq — Відповісти на поширені питання\n"
        "/order — Допомогти оформити замовлення\n"
        "/contacts — Надати контакти магазину\n"
        "/feedback — Прийняти відгук або запитання"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# Команда /catalog
@bot.message_handler(commands=['catalog'])
def catalog(message):
    markup = types.InlineKeyboardMarkup(row_width=2)

    btn1 = types.InlineKeyboardButton('Футболки', callback_data='category_tshirts')
    btn2 = types.InlineKeyboardButton('Куртки', callback_data='category_jackets')
    btn3 = types.InlineKeyboardButton('Взуття', callback_data='category_shoes')
    btn4 = types.InlineKeyboardButton('Аксесуари', callback_data='category_accessories')

    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, 'Оберіть категорію товарів:', reply_markup=markup)

# Обробка натискань на кнопки
@bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def callback_inline(call):
    category = call.data[len('category_'):]

    if category == 'tshirts':
        text = "Наші футболки:\n1. Біла футболка — 500 грн\n2. Чорна футболка — 500 грн"
    elif category == 'jackets':
        text = "Наші куртки:\n1. Дощовик — 1000 грн\n2. Зимова куртка — 2050 грн"
    elif category == 'shoes':
        text = "Наше взуття:\n1. Кросівки — 1299 грн\n2. Чоботи — 1599 грн"
    elif category == 'accessories':
        text = "Наші аксесуари:\n1. Ремінь — 200 грн\n2. Шапка — 240 грн"
    else:
        text = "Категорія не знайдена."

    bot.send_message(call.message.chat.id, text)

#Photo
@bot.message_handler(content_types=['photo'])
def handler_photo(message):
    bot.send_message(message.chat.id, 'Якщо хочеш поради - напиши, що саме шукаєш або що тобі подобається')

@bot.message_handler(content_types=['video'])
def handle_video(message):
    bot.send_message(message.chat.id, 'Якщо це приклад стилю чи запитання - ми його розглянемо')


# Повідомлення без команди
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def info(message):
    bot.send_message(message.chat.id, 'Введіть команду /start щоб почати роботу зі мною\n'
                                            'Прийняти відгук або запитання /feedback\n')


# Запуск бота
bot.polling(none_stop=True)