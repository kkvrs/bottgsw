import logging
from telegram import Update, Bot, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram.error import TelegramError

# Ваш токен бота
BOT_TOKEN = "7333891602:AAGRTxjd-McUFCvYCklBfX4oaECr-TEuzGM"
GROUP_CHAT_ID = -1002210985589  # Ваш ID чата группы, начиная с -100 если это супер-группа

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем стадии разговора
FULL_NAME, AGE, PHONE_NUMBER = range(3)

def check_user_registered(user_id: int) -> bool:
    with open("users.txt", "r", encoding='utf-8') as f:
        for line in f:
            data = line.split(',')
            if int(data[3]) == user_id:
                return True
    return False

def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    username = update.effective_user.username

    # Проверка, зарегистрирован ли пользователь
    if check_user_registered(user_id):
        update.message.reply_text('Вы уже зарегистрированы.')
        return ConversationHandler.END

    # Сохранение ID и логина пользователя
    context.user_data['user_id'] = user_id
    context.user_data['username'] = username

    update.message.reply_text('Добро пожаловать! Пожалуйста, введите вашу Фамилию Имя Отчество.')
    return FULL_NAME

def get_full_name(update: Update, context: CallbackContext) -> int:
    context.user_data['full_name'] = update.message.text
    update.message.reply_text('Пожалуйста, введите ваш возраст.')
    return AGE

def get_age(update: Update, context: CallbackContext) -> int:
    context.user_data['age'] = update.message.text
    contact_button = KeyboardButton('Поделиться номером телефона', request_contact=True)
    update.message.reply_text(
        'Пожалуйста, поделитесь вашим номером телефона.',
        reply_markup=ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True)
    )
    return PHONE_NUMBER

def get_phone_number(update: Update, context: CallbackContext) -> int:
    contact = update.message.contact
    if contact:
        context.user_data['phone_number'] = contact.phone_number

        # Получение сохраненных данных
        full_name = context.user_data['full_name']
        age = context.user_data['age']
        phone_number = context.user_data['phone_number']

        # Получение ID и логина пользователя
        user_id = context.user_data['user_id']
        username = context.user_data['username']

        # Сохранение данных о пользователе
        user_data = f"{full_name}, {age}, {phone_number}, {user_id}, {username}\n"
        with open("users.txt", "a", encoding='utf-8') as f:
            f.write(user_data)

        try:
            # Создание одноразовой ссылки-приглашения
            bot = Bot(BOT_TOKEN)
            invite_link = bot.create_chat_invite_link(GROUP_CHAT_ID, member_limit=1)

            # Уведомление и логирование
            update.message.reply_text(f'Регистрация завершена! Вот ваша ссылка для присоединения к группе: {invite_link.invite_link}')

        except TelegramError as e:
            # Логирование ошибки
            logger.error(f"Ошибка создания ссылки для приглашения: {e}")
            update.message.reply_text('Произошла ошибка при создании ссылки приглашения. Пожалуйста, повторите попытку позже.')

        return ConversationHandler.END

    else:
        update.message.reply_text('Пожалуйста, поделитесь вашим номером телефона.')
        return PHONE_NUMBER

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Регистрация отменена.')
    return ConversationHandler.END

def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FULL_NAME: [MessageHandler(Filters.text & ~Filters.command, get_full_name)],
            AGE: [MessageHandler(Filters.text & ~Filters.command, get_age)],
            PHONE_NUMBER: [MessageHandler(Filters.contact, get_phone_number)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
