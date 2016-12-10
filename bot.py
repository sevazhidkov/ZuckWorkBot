import os
import json
import redis
import telegram

from api import BackendApi

NEXT_BUTTON = 'Далее ➡️'
PREVIOUS_BUTTON = 'Назад ⬅️'
THATS_ALL_BUTTON = 'Всё, я выбрал ✅'
COURSE_MESSAGE = '*{title}*\n\n🕙 Время: _{time}_\n💬 Язык: _{language}_\n\n{link}'


class Bot:
    def __init__(self, telegram_client):
        self.telegram = telegram_client
        self.redis = redis.from_url(os.environ['REDIS_URL'])
        self.api = BackendApi()

    def process_update(self, update):
        if update.message:
            self.process_message(update.message)
        if update.callback_query:
            self.process_callback_query(update.callback_query)

    def process_message(self, message):
        handler_name = self.redis.get('user:{}:current_handler'.format(message.from_user.id))
        if not handler_name:
            keyboard = [[x] for x in self.api.get_vacancies()[:3]]
            keyboard += [[NEXT_BUTTON]]
            self.redis.set('user:{}:first_vacancy'.format(message.from_user.id), 0)
            self.redis.set('user:{}:current_handler'.format(message.from_user.id), 'choose_vacancy')
            message.reply_text('Хэй! Ну что, пропихнуть тебя в Facebook? Кем хочешь стать?',
                               reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
            self.redis.set('user:{}:cur_skills'.format(message.from_user.id), json.dumps([]))
            return

        handler_name = handler_name.decode('utf-8')
        if handler_name == 'choose_vacancy' and message.text == NEXT_BUTTON:
            cur = int(self.redis.get('user:{}:first_vacancy'.format(message.from_user.id)))
            result = self.api.get_vacancies()
            keyboard = [[x] for x in result[cur + 3:cur + 6]]
            if len(result) > cur + 6:
                keyboard += [[PREVIOUS_BUTTON, NEXT_BUTTON]]
            else:
                keyboard += [[PREVIOUS_BUTTON]]
            self.redis.set('user:{}:first_vacancy'.format(message.from_user.id), cur + 3)
            message.reply_text('Держи!',
                               reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
            return
        if handler_name == 'choose_vacancy' and message.text == PREVIOUS_BUTTON:
            cur = int(self.redis.get('user:{}:first_vacancy'.format(message.from_user.id)))
            keyboard = [[x] for x in self.api.get_vacancies()[cur - 3:cur]]
            if cur - 3 != 0:
                keyboard += [[PREVIOUS_BUTTON, NEXT_BUTTON]]
            else:
                keyboard += [[NEXT_BUTTON]]
            self.redis.set('user:{}:first_vacancy'.format(message.from_user.id), cur - 3)
            message.reply_text('Держи!',
                               reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
            return
        if handler_name == 'choose_vacancy':
            if message.text not in self.api.get_vacancies():
                keyboard = [[x] for x in self.api.get_vacancies()[:3]]
                keyboard += [[NEXT_BUTTON]]
                self.redis.set('user:{}:first_vacancy'.format(message.from_user.id), 0)
                message.reply_text('Ты о чём?',
                                   reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
                return
            self.redis.set('user:{}:vacancy'.format(message.from_user.id), message.text)
            self.redis.set('user:{}:current_handler'.format(message.from_user.id), 'choose_skills')
            result = self.api.get_topics()
            keyboard = [[x] for x in result]
            keyboard += [[THATS_ALL_BUTTON]]
            message.reply_text('Выбери какими навыками и знаниями ты уже владеешь, чтобы '
                               'я мог построить программу специально для тебя',
                               reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
            return

        if handler_name == 'choose_skills' and message.text != THATS_ALL_BUTTON:
            if message.text not in self.api.get_topics():
                self.redis.set('user:{}:current_handler'.format(message.from_user.id), 'choose_skills')
                result = self.api.get_topics()
                keyboard = [[x] for x in self.api.get_topics()]
                keyboard += [[THATS_ALL_BUTTON]]
                message.reply_text('Ты о чём? Выбери то, что знаешь!',
                                   reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
                self.redis.set('user:{}:cur_skills'.format(message.from_user.id), json.dumps([]))
                return
            cur_skills = []
            saved_skills = self.redis.get('user:{}:cur_skills'.format(message.from_user.id))
            if saved_skills:
                cur_skills = json.loads(saved_skills.decode('utf-8'))
            cur_skills.append(message.text)
            self.redis.set('user:{}:cur_skills'.format(message.from_user.id), json.dumps(cur_skills))
            result = self.api.get_topics()
            keyboard = [[x] for x in result if x not in cur_skills]
            keyboard += [[THATS_ALL_BUTTON]]
            message.reply_text('Супер! Что-то еще?',
                               reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
            return

        if handler_name == 'choose_skills':
            message.reply_text('Офигенно, ты многого добьешься ❤️', reply_markup=telegram.ReplyKeyboardHide())
            message.reply_text('Сейчас я подумаю и построю тебе индивидуальную программу 🤔',
                               reply_markup=telegram.ReplyKeyboardHide())
            vacancy = self.redis.get('user:{}:vacancy'.format(message.from_user.id)).decode('utf-8')
            saved_skills = json.loads(
                self.redis.get('user:{}:cur_skills'.format(message.from_user.id)).decode('utf-8')
            )
            result = self.api.generate_program(vacancy, saved_skills)
            self.redis.delete('user:{}:current_handler'.format(message.from_user.id))

            self.redis.set('user:{}:program'.format(message.from_user.id), json.dumps(result))
            self.redis.set('user:{}:cur'.format(message.from_user.id), '0')
            keyboard = [[telegram.InlineKeyboardButton('Посетить курс 🌐', url=result[0]['link'])],
                        [telegram.InlineKeyboardButton(NEXT_BUTTON, callback_data='next')]]
            message.reply_text(COURSE_MESSAGE.format(
                title=result[0]['title'],
                time=result[0]['time'],
                language=result[0]['language'],
                link=result[0]['link']
            ), reply_markup=telegram.InlineKeyboardMarkup(keyboard), parse_mode='markdown')

    def process_callback_query(self, query):
        print(query)


telegram_client = telegram.Bot(os.environ['BOT_TOKEN'])
bot = Bot(telegram_client)

bot.telegram.setWebhook('')
try:
    update_id = telegram_client.getUpdates()[0].update_id
except IndexError:
    update_id = None

while True:
    try:
        for update in telegram_client.getUpdates(offset=update_id, timeout=10):
            update_id = update.update_id + 1
            bot.process_update(update)
    except telegram.error.Unauthorized:
        update_id += 1
