import os
from dotenv import load_dotenv
import telebot
from telebot import types
import sqlite3

# Завантаження змінних із .env файлу
load_dotenv()

# Отримуємо токен бота
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

# Ініціалізуємо бота
bot = telebot.TeleBot(TOKEN)

# Створення таблиці, якщо не існує, з унікальним telegram_id
def create_users_table():
    try:
        conn = sqlite3.connect('chatbot.db')
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            user_pass TEXT)
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite error on create_users_table: {e}")
    finally:
        conn.close()

# Додавання користувача, якщо його ще немає в базі, по telegram_id
def add_user_if_not_exist(telegram_id, full_name):
    try:
        conn = sqlite3.connect("chatbot.db")
        c = conn.cursor()
        c.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (telegram_id,))
        user = c.fetchone()
        if not user:
            c.execute("INSERT INTO users (telegram_id, name, user_pass) VALUES (?, ?, ?)", (telegram_id, full_name, "default"))
            conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite error on add_user_if_not_exist: {e}")
    finally:
        conn.close()

# Збереження даних користувача для підбору розміру
user_data = {}
user_gender = {}

# Команда /start + додавання користувача в базу
@bot.message_handler(commands=['start'])
def start(message):
    first = message.from_user.first_name or ''
    last = message.from_user.last_name or ''
    full_name = f"{first} {last}".strip()
    telegram_id = message.from_user.id

    add_user_if_not_exist(telegram_id, full_name)

    bot.send_message(
        message.chat.id,
        f"Привіт! {full_name}!\n"
        "Я — твій консультант з одягу та доставки.\n"
        "Допоможу вибрати круті речі, знайти свій розмір і швидко організувати доставку.\n"
        "Якщо маєш питання — пиши /feedback, завжди поруч! 😊\n"
        "Також можеш подивитися, що я можу зробити для тебе /help"
    )

# Команда /help - Список доступних команд
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
        "/feedback — Прийняти відгук або запитання\n"
        "✵✵✵\n"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# Команда /catalog - Показ категорії товарів
@bot.message_handler(commands=['catalog'])
def catalog(message):
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Кнопки з категоріями
    btn1 = types.InlineKeyboardButton('Футболки', callback_data='category_tshirts')
    btn2 = types.InlineKeyboardButton('Куртки', callback_data='category_jackets')
    btn3 = types.InlineKeyboardButton('Взуття', callback_data='category_shoes')
    btn4 = types.InlineKeyboardButton('Аксесуари', callback_data='category_accessories')

    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, 'Оберіть категорію товарів:', reply_markup=markup)

# Обробка натискань на кнопки категорій
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

# Команда /sizes - Підбір розміру
@bot.message_handler(commands=['sizes'])
def sizes(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Жінка'), types.KeyboardButton('Чоловік'))
    msg = bot.send_message(message.chat.id, 'Оберіть, будь ласка, ваш пол:', reply_markup=markup)
    bot.register_next_step_handler(msg, after_gender_choice)

# Обробка вибору статі
def after_gender_choice(message):
    gender_text = message.text
    if gender_text not in ['Жінка', 'Чоловік']:
        msg = bot.send_message(message.chat.id, 'Будь ласка, оберіть зі списку, натиснувши на кнопку.')
        bot.register_next_step_handler(msg, after_gender_choice)
        return
    user_gender[message.from_user.id] = gender_text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Розрахувати розмір'), types.KeyboardButton('Подивитися таблицю розмірів'))
    msg = bot.send_message(message.chat.id, 'Оберіть дію:', reply_markup=markup)
    bot.register_next_step_handler(msg, after_size_option)

# Обробка вибору дії після вибору статі
def after_size_option(message):
    text = message.text
    if text == 'Розрахувати розмір':
        msg = bot.send_message(message.chat.id, "Введіть ваш зріст у сантиметрах (наприклад, 168):")
        bot.register_next_step_handler(msg, ask_weight)
    elif text == 'Подивитися таблицю розмірів':
        user_id = message.from_user.id
        gender_text = user_gender.get(user_id)
        if not gender_text:
            bot.send_message(message.chat.id, "Спочатку оберіть ваш пол командою /sizes")
            return

        if gender_text == 'Жінка':
            photo_path = 'images/size_women.jpg'
        else:
            photo_path = 'images/size_men.jpg'

        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption="Ось таблиця розмірів")
        else:
            bot.send_message(message.chat.id, "Вибачте, таблиця наразі недоступна.")
    else:
        msg = bot.send_message(message.chat.id, 'Будь ласка, оберіть дію, натиснувши на кнопку.')
        bot.register_next_step_handler(msg, after_size_option)

# Запит ваги після зросту
def ask_weight(message):
    chat_id = message.chat.id
    try:
        height = int(message.text)
        if not (50 <= height <= 250):
            raise ValueError()
        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]['height'] = height
    except ValueError:
        msg = bot.send_message(chat_id, "Будь ласка, введіть коректний ріст числом (наприклад, 168) і спробуйте ще раз:")
        bot.register_next_step_handler(msg, ask_weight)
        return
    msg = bot.send_message(chat_id, "Тепер введіть вашу вагу в кілограмах (наприклад, 60):")
    bot.register_next_step_handler(msg, calculate_size)

# Розрахунок розміру по ІМТ
def calculate_size(message):
    chat_id = message.chat.id
    try:
        weight = int(message.text)
        if not (20 <= weight <= 300):
            raise ValueError()
        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]['weight'] = weight
    except ValueError:
        msg = bot.send_message(chat_id, 'Будь ласка, введіть конкретну вагу числом (наприклад, 60) і спробуйте ще раз.')
        bot.register_next_step_handler(msg, calculate_size)
        return

    height = user_data[chat_id].get('height')
    weight = user_data[chat_id].get('weight')
    gender = user_gender.get(message.from_user.id, 'Жінка')  # дефолт — Жінка

    height_m = height / 100
    bmi = weight / (height_m ** 2)

    if gender == "Жінка":
        if bmi < 18.5:
            size = 'XS'
        elif bmi < 24.9:
            size = 'S - M'
        elif bmi < 29.9:
            size = 'L'
        else:
            size = 'XL і більше'
        photo_path = 'images/size_women.jpg'
    else:
        if bmi < 18.5:
            size = 'S'
        elif bmi < 24.9:
            size = 'M'
        elif bmi < 29.9:
            size = 'L'
        else:
            size = 'XL і більше'
        photo_path = 'images/size_men.jpg'

    bot.send_message(chat_id, f"ІМТ: {bmi:.1f}\nРекомендований розмір одягу: *{size}*", parse_mode='Markdown')

    if os.path.exists(photo_path):
        with open(photo_path, 'rb') as photo:
            bot.send_photo(chat_id, photo)
    else:
        bot.send_message(chat_id, "Фото з розмірною сіткою тимчасово недоступне")

    # Очищення даних користувача після завершення
    user_data.pop(chat_id, None)
    user_gender.pop(message.from_user.id, None)

# Популярные вопросы
@bot.message_handler(commands=['faq'])
def faq(message):
    bot.send_message(message.chat.id, """
1. Як дізнатися свій розмір одягу?  
Виміряй груди, талію та стегна сантиметром і звір із таблицею розмірів.

2. Що робити, якщо я між двома розмірами?  
Краще обрати більший — його легше підганяти, ніж носити тісний одяг.

3. Чим відрізняється S від 36 розміру?  
S — буквене позначення, 36 — цифрове. Приблизно відповідають, але залежить від бренду.

4. Як обрати одяг за зростом і вагою?  
Можна орієнтуватися на таблиці ІМТ, але точніше — за обхватами в сантиметрах.

5. Який одяг візуально струнить?  
Однотонний темний одяг, вертикальні лінії, V-подібний виріз.

6. Що підійде дівчині з широкими стегнами?  
Світлий або обʼємний верх, однотонний низ прямого крою.

7. Як зрозуміти, чи підійде річ без примірки?  
Звір свої мірки з таблицею, перевір заміри виробу та склад тканини.

8. Чим бавовна відрізняється від поліестеру?  
Бавовна — натуральна, дихає. Поліестер — синтетика, менше мнеться і дешевший.

9. Як доглядати за одягом, щоб не зіпсувати?  
Дотримуйся вказівок на ярлику: температура прання, сушка, прасування.

10. Як зібрати базовий гардероб?  
Обирай прості фасони, нейтральні кольори і речі, що легко поєднуються між собою.
""")

# Контактні дані
@bot.message_handler(commands=['contacts'])
def contacts(message):
    bot.send_message(message.chat.id, """
Контактна інформація:
Адреса: вул. Модна, 12, Київ  
Телефон: +38 (044) 123-45-67  
Email: info@fashion-shop.com  
Графік роботи: Пн–Сб з 10:00 до 19:00  
Сайт: fashion-shop.com  
Це демо-бот для портфоліо. Дані – умовні.
""")

# Допомога оформити замовлення
@bot.message_handler(commands=['order'])
def order(message):
    bot.send_message(message.chat.id,
"Щоб оформити замовлення:\n\n"
"1. Оберіть товар (напишіть назву або код)\n"
"2. Вкажіть розмір та колір\n"
"3. Напишіть ваше ім’я, номер телефону та місто доставки\n\n"
"Після цього ми підтвердимо замовлення протягом 24 годин.\n\n"
"Це демо-бот. Реальне замовлення не оформлюється.", parse_mode="Markdown")

# Розповісти про доставку і оплату
@bot.message_handler(commands=['delivery'])
def delivery(message):
    bot.send_message(message.chat.id,
"🛒 Щоб оформити замовлення:\n\n"
"1. Оберіть товар (напишіть назву або код)\n"
"2. Вкажіть розмір та колір\n"
"3. Напишіть ваше ім’я, номер телефону та місто доставки\n\n"
"Після цього ми підтвердимо замовлення протягом 24 годин.\n\n"
"Це демо-бот. Реальне замовлення не оформлюється.", parse_mode="Markdown")

# Обробка фото від користувача
@bot.message_handler(content_types=['photo'])
def handler_photo(message):
    bot.send_message(message.chat.id, 'Якщо хочеш поради - напиши, що саме шукаєш або що тобі подобається')

# Обробка відео від користувача
@bot.message_handler(content_types=['video'])
def handle_video(message):
    bot.send_message(message.chat.id, 'Якщо це приклад стилю чи запитання, ми його розглянемо')

# Повідомлення без команди
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def info(message):
    bot.send_message(message.chat.id, 'Введіть команду /start щоб почати роботу зі мною\n'
                                    'Прийняти відгук або запитання /feedback\n')

# Стан зворотного зв'язку для користувачів
user_feedback_state = {}

@bot.message_handler(commands=['feedback'])
def handle_feedback(message):
    bot.send_message(message.chat.id, 'Напишіть свій відгук або запитання\n')
    user_feedback_state[message.from_user.id] = 'awaiting_feedback'

@bot.message_handler(func=lambda message: user_feedback_state.get(message.from_user.id) == 'awaiting_feedback')
def receive_feedback(message):
    feedback_text = message.text.strip()
    user = message.from_user

    if not feedback_text:
        bot.send_message(message.chat.id, "Будь ласка, напишіть щось конкретне 🙂")
        return

    try:
        with open('feedback.txt', 'a', encoding='utf-8') as f:
            f.write(f"Від {user.first_name} (@{user.username if user.username else 'немає username'}):\n")
            f.write(f"{feedback_text}\n\n")
    except Exception as e:
        print(f"Error writing feedback: {e}")

    bot.send_message(message.chat.id, "Дякуємо за ваш відгук!")
    user_feedback_state.pop(message.from_user.id, None)

# Створюємо таблицю, якщо потрібно
create_users_table()

# Запуск бота
bot.polling(none_stop=True)
