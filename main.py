import requests
import re
from datetime import datetime
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, filters, CallbackQueryHandler,ConversationHandler


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

userGROUP = ''
userSEMESTER = ''
SCHEDULE_URL = ''
weekNUM = 0
Days = ["MON","TUE","WED",'THU','FRI','SAT','SUN']
nextLessonFlag = False

FIRST, SECOND, THIRD, FOUTH, FIFTH, SIXTH = range(6)

class Bot():

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Доброго времени суток, расписание какой группы вы хотите узнать сегодня?")
        return FIRST


    async def getGroupAndSemINFO(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global userGROUP
        userGROUP = update.message.text
        await update.message.reply_text(f"Ваша группа изменена на {userGROUP}")
        semesterKeyboard = [
            [
                InlineKeyboardButton("Осенний", callback_data='autumn'),
                InlineKeyboardButton("Весенний", callback_data='spring'),
            ]
        ]
        SKreply_markup = InlineKeyboardMarkup(semesterKeyboard)
        await update.message.reply_text("Какой семестр вам интересен?", reply_markup=SKreply_markup)
        return SECOND



    async def getGroupAndSemINFO_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global userSEMESTER
        userSEMESTER = update.callback_query
        await userSEMESTER.answer()
        await update.callback_query.message.edit_text(f"Выбранный семестр {userSEMESTER.data}")
        userSEMESTER = str(userSEMESTER.data)

        weekKeyboard = [
            [
                InlineKeyboardButton("Первую", callback_data='1'),
                InlineKeyboardButton("Вторую", callback_data='2'),
                InlineKeyboardButton("Обе", callback_data='0'),
            ]
        ]
        WKreply_markup = InlineKeyboardMarkup(weekKeyboard)
        await update.callback_query.message.reply_text("Расписание на какую неделю вам показать?", reply_markup=WKreply_markup)

        return THIRD

    async def getWeekNum_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global weekNUM
        weekNUM = update.callback_query
        await weekNUM.answer()
        await update.callback_query.message.edit_text(f"Выбранная неделя {weekNUM.data}")
        weekNUM = int(weekNUM.data)

        await update.callback_query.message.reply_text(
            " Чтобы узнать ближайшее занятие, введите /near \n\n Чтобы узнать расписание на определенный день, введите /day \n\n "
            "Чтобы узнать расписание на завтра, введите /tomorrow \n\n Чтобы узнать расписание на всю неделю, введите /week")
        return FOUTH



    async def getNextLesson(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global SCHEDULE_URL, nextLessonFlag
        nextLessonFlag = True
        SCHEDULE_URL = f"https://digital.etu.ru/api/mobile/schedule?weekDay=&subjectType=&groupNumber={userGROUP}&joinWeeks=false&season={userSEMESTER}&year=2024"
        await update.message.reply_text("Чтобы подтвердить выбор, введите любой символ")
        return SIXTH


    async def getDaySchedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        dayKeyboard = [
            [
                InlineKeyboardButton("Понедельник", callback_data='MON'),
                InlineKeyboardButton("Вторник", callback_data='TUE'),
                InlineKeyboardButton("Среда", callback_data='WED'),],
            [    InlineKeyboardButton("Четверг", callback_data='THU'),
                InlineKeyboardButton("Пятница", callback_data='FRI'),
                InlineKeyboardButton("Суббота", callback_data='SAT'),],
            [    InlineKeyboardButton("Воскресенье", callback_data='SUN'),
            ]
        ]
        DKreply_markup = InlineKeyboardMarkup(dayKeyboard)
        await update.message.reply_text("Какой день вам интересен?", reply_markup=DKreply_markup)
        return FIFTH


    async def getDaySchedule_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global SCHEDULE_URL
        dayCase = update.callback_query
        await dayCase.answer()
        await update.callback_query.message.edit_text(f"Выбранный день {dayCase.data}")
        await update.callback_query.message.reply_text("Чтобы подтвердить выбор, введите любой символ")
        SCHEDULE_URL = f"https://digital.etu.ru/api/mobile/schedule?weekDay={dayCase.data}&subjectType=&groupNumber={userGROUP}&joinWeeks=false&season={userSEMESTER}&year=2024"
        return SIXTH




    async def getTomorrowSchedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global SCHEDULE_URL
        now = datetime.now()
        data = datetime.weekday(now)+1
        if data == 7:
            data = 0
        SCHEDULE_URL = f"https://digital.etu.ru/api/mobile/schedule?weekDay={Days[data]}&subjectType=&groupNumber={userGROUP}&joinWeeks=false&season={userSEMESTER}&year=2024"
        await update.message.reply_text("Чтобы подтвердить выбор, введите любой символ")
        return SIXTH





    async def getWeekSchedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global SCHEDULE_URL
        SCHEDULE_URL = f"https://digital.etu.ru/api/mobile/schedule?weekDay=&subjectType=&groupNumber={userGROUP}&joinWeeks=false&season={userSEMESTER}&year=2024"
        await update.message.reply_text("Чтобы подтвердить выбор, введите любой символ")
        return SIXTH




    async def getResponce(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global nextLessonFlag
        response = requests.get(SCHEDULE_URL)
        now = datetime.now()
        if response.status_code == 200:
            data = response.text
            resultNext = []

            pattern = r'\{"name":"(.*?)","lessons":\[(.*?)\]\}'
            matches = re.findall(pattern, data)

            for match in matches:
                result = []
                day_name, lessons_data = match
                if nextLessonFlag != True:
                    await update.message.reply_text(f"✨{day_name}✨")

                lesson_pattern = r'\{"teacher":"(.*?)","second_teacher":"(.*?)","subjectType":"(.*?)","week":"(.*?)","name":"(.*?)","start_time":"(.*?)","end_time":"(.*?)".*?\}'
                lessons = re.findall(lesson_pattern, lessons_data)

                for lesson in lessons:
                    teacher, second_teacher, subject_type, week_parity, subject, start_time, end_time = lesson
                    text = (f"Неделя: {week_parity},\nПредмет: {subject}, \nНачало: {start_time}, \nКонец: {end_time}, \nПреподаватель: {teacher}")
                    if nextLessonFlag == True:
                        resultNext.append(lesson)
                    result.append(lesson)
                for lesson in result:
                    if int(lesson[3]) == weekNUM:
                        await update.message.reply_text(f"Неделя: {lesson[3]},\nПредмет: {lesson[4]}, \nНачало: {lesson[5]}, \nКонец: {lesson[6]}, \nПреподаватель: {lesson[0]}")


                if nextLessonFlag == True and matches[datetime.weekday(now)] == match:
                    counter = 0
                    for lesson in resultNext:
                        lessonTimeStart = str(lesson[5])
                        lessonTimeEnd = str(lesson[6])
                        if int(lessonTimeEnd[0:2]+lessonTimeEnd[3:5]) >= int(str(now.hour)+str(now.minute)):
                            await update.message.reply_text(f"Неделя: {lesson[3]},\nПредмет: {lesson[4]}, \nНачало: {lesson[5]}, \nКонец: {lesson[6]}, \nПреподаватель: {lesson[0]}")
                            counter+=1
                            break
                    if counter == 0:
                        await update.message.reply_text("Сегодня больше нет пар")
            nextLessonFlag = False
        else:
            print(f"Ошибка при запросе: {response.status_code}")
        return ConversationHandler.END

if __name__ == "__main__":
    APIfile = open('botAPI.txt')
    API = APIfile.read()
    APIfile.close()

    scheduleBot = Bot()

    application = ApplicationBuilder().token(API).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', scheduleBot.start)],
        states={
            FIRST: [MessageHandler(filters.TEXT, scheduleBot.getGroupAndSemINFO)],
            SECOND: [CallbackQueryHandler(scheduleBot.getGroupAndSemINFO_callback)],
            THIRD: [CallbackQueryHandler(scheduleBot.getWeekNum_callback)],
            FOUTH: [(CommandHandler('near', scheduleBot.getNextLesson)),
                    (CommandHandler('day', scheduleBot.getDaySchedule)),
                    (CommandHandler('tomorrow', scheduleBot.getTomorrowSchedule)),
                    (CommandHandler('week', scheduleBot.getWeekSchedule)),
                    ],
            FIFTH: [CallbackQueryHandler(scheduleBot.getDaySchedule_callback)],
            SIXTH:[MessageHandler(filters.TEXT, scheduleBot.getResponce)],
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler)
    application.run_polling()
