import os
import sys
import time
import json

import redis
import flask
import telegram

from api import BackendApi

NEXT_BUTTON = 'Далее ➡️'
PREVIOUS_BUTTON = 'Назад ⬅️'
THATS_ALL_BUTTON = 'Всё, я выбрал ✅'
COURSE_MESSAGE = '*{title}*\n\n🕙 Время: _{time}_\n💬 Язык: _{language}_\n\n{link}'

app = flask.Flask(__name__)


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
            keyboard = [[x] for x in self.api.get_vacancies().keys()]
            self.redis.set('user:{}:first_vacancy'.format(message.from_user.id), 0)
            self.redis.set('user:{}:current_handler'.format(message.from_user.id), 'choose_division')
            message.reply_text('Хэй! Ну что, пропихнуть тебя в Facebook? Где хочешь работать?',
                               reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
            self.redis.set('user:{}:cur_skills'.format(message.from_user.id), json.dumps([]))
            return

        handler_name = handler_name.decode('utf-8')
        if handler_name == 'choose_division':
            result = self.api.get_vacancies()
            if message.text not in result.keys():
                keyboard = [[x] for x in result.keys()]
                message.reply_text('Ты о чём?', reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
                return
            self.redis.set('user:{}:division'.format(message.from_user.id), message.text)
            keyboard = [[x] for x in result[message.text][0:3]]
            keyboard += [[NEXT_BUTTON]]
            self.redis.set('user:{}:current_handler'.format(message.from_user.id), 'choose_vacancy')
            message.reply_text('Окей, а кем хочешь работать?',
                               reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
            return
        if handler_name == 'choose_vacancy' and message.text == NEXT_BUTTON:
            user_division = self.redis.get('user:{}:division'.format(message.from_user.id)).decode('utf-8')
            cur = int(self.redis.get('user:{}:first_vacancy'.format(message.from_user.id)))
            result = self.api.get_vacancies()[user_division]
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
            user_division = self.redis.get('user:{}:division'.format(message.from_user.id)).decode('utf-8')
            cur = int(self.redis.get('user:{}:first_vacancy'.format(message.from_user.id)))
            keyboard = [[x] for x in self.api.get_vacancies()[user_division][cur - 3:cur]]
            if cur - 3 != 0:
                keyboard += [[PREVIOUS_BUTTON, NEXT_BUTTON]]
            else:
                keyboard += [[NEXT_BUTTON]]
            self.redis.set('user:{}:first_vacancy'.format(message.from_user.id), cur - 3)
            message.reply_text('Держи!',
                               reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
            return
        if handler_name == 'choose_vacancy':
            user_division = self.redis.get('user:{}:division'.format(message.from_user.id)).decode('utf-8')
            if message.text not in self.api.get_vacancies()[user_division]:
                keyboard = [[x] for x in self.api.get_vacancies()[user_division][:3]]
                keyboard += [[NEXT_BUTTON]]
                self.redis.set('user:{}:first_vacancy'.format(message.from_user.id), 0)
                message.reply_text('Ты о чём?',
                                   reply_markup=telegram.ReplyKeyboardMarkup(keyboard))
                return
            message.reply_text('Отлично, мне давно нужны были такие специалисты ')
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
        result = json.loads(self.redis.get('user:{}:program'.format(query.from_user.id)).decode('utf-8'))
        if query.data == 'next':
            program = json.loads(
                self.redis.get('user:{}:program'.format(query.from_user.id)).decode('utf-8')
            )
            cur = int(self.redis.get('user:{}:cur'.format(query.from_user.id))) + 1
        elif query.data == 'previous':
            program = json.loads(
                self.redis.get('user:{}:program'.format(query.from_user.id)).decode('utf-8')
            )
            cur = int(self.redis.get('user:{}:cur'.format(query.from_user.id))) - 1
        bot.telegram.editMessageText(
            text=COURSE_MESSAGE.format(
                title=result[cur]['title'],
                time=result[cur]['time'],
                language=result[cur]['language'],
                link=result[cur]['link']
            ),
            parse_mode=telegram.ParseMode.MARKDOWN,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            disable_web_page_preview=True
        )
        keyboard = [[telegram.InlineKeyboardButton('Посетить курс 🌐', url=result[cur]['link'])],
                    []]
        if cur != 0:
            keyboard[1].append(telegram.InlineKeyboardButton(PREVIOUS_BUTTON, callback_data='previous'))
        if cur != len(result) - 1:
            keyboard[1].append(telegram.InlineKeyboardButton(NEXT_BUTTON, callback_data='next'))
        bot.telegram.editMessageReplyMarkup(
            reply_markup=telegram.InlineKeyboardMarkup(keyboard),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
        self.redis.set('user:{}:cur'.format(query.from_user.id), cur)
        self.telegram.answerCallbackQuery(callback_query_id=query.id)


@app.route('/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(flask.request.get_json(force=True), bot.telegram)
    bot.process_update(update)
    return 'ok'


telegram_client = telegram.Bot(os.environ['BOT_TOKEN'])
bot = Bot(telegram_client)

if len(sys.argv) > 1 and sys.argv[1] == 'polling':
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
        except (telegram.error.Unauthorized, telegram.error.BadRequest):
            update_id += 1
    exit()

try:
    bot.telegram.setWebhook('https://zuckworkbot.herokuapp.com/webhook')
except telegram.error.RetryAfter:
    time.sleep(1)
    bot.telegram.setWebhook('https://zuckworkbot.herokuapp.com/webhook')
