from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from shared.utils import db_nosql

def main(locale):
    # Структура меню в виде списка строк
    menu_layout = [
        [locale.REPLY_MAIN_REMINDERS(), locale.REPLY_MAIN_MICRO(), locale.REPLY_MAIN_GROUPS()],
        [locale.REPLY_MAIN_RATINGS(), locale.REPLY_MAIN_PROFILE(), locale.REPLY_MAIN_HELP()]
    ]
    
    # Преобразование в клавиатуру
    keyboard = [
        [KeyboardButton(text=text) for text in row]
        for row in menu_layout
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

async def reply_profile(locale):
    # Структура меню в виде списка строк
    menu_layout = [
        [locale.REPLY_PROF_FRIENDS(), locale.REPLY_PROF_GOALS(), locale.REPLY_PROF_SETTINGS()],
        [locale.REPLY_PROF_PREMIUM(), locale.REPLY_PROF_REF(), locale.REPLY_MAIN()]
    ]
    
    # Преобразование в клавиатуру
    keyboard = [
        [KeyboardButton(text=text) for text in row]
        for row in menu_layout
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


    
def reminders(locale):
    # Структура меню в виде списка строк
    menu_layout = [
        [locale.REPLY_REM_ADD(), locale.REPLY_REM_DELETE()],
        [locale.REPLY_MAIN()]
    ]
    
    # Преобразование в клавиатуру
    keyboard = [
        [KeyboardButton(text=text) for text in row]
        for row in menu_layout
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )
    
    
def inline_reminders(locale):
    action_map = {
        locale.INLINE_REM_TIME_30(): "remind_30",
        locale.INLINE_REM_TIME_60(): "remind_60",
        locale.INLINE_REM_TIME_120(): "remind_120",
        locale.INLINE_REM_CUSTOM_TIME(): "remind_custom",
        locale.INLINE_REM_CANCEL(): "back_remind"
    }
    
    menu_layout = [
        [locale.INLINE_REM_TIME_30(), locale.INLINE_REM_TIME_60(), locale.INLINE_REM_TIME_120()],
        [locale.INLINE_REM_CUSTOM_TIME(), locale.INLINE_REM_CANCEL()]
    ]
    
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=action_map[text]) for text in row]
        for row in menu_layout
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def inline_reminders_when(locale):
    action_map = {
        locale.INLINE_REM_ONCE(): "remind_once",
        locale.INLINE_REM_DAILY(): "remind_daily",
        locale.INLINE_REM_WEEKLY(): "remind_weekly",
        locale.INLINE_REM_MONTHLY(): "remind_monthly",
        locale.INLINE_REM_CUSTOM_REPEAT(): "remind_repeat_custom",
     
        locale.INLINE_REM_CANCEL(): "back_remind"
    }
    
    menu_layout = [
        [locale.INLINE_REM_ONCE(), locale.INLINE_REM_DAILY()],
        [locale.INLINE_REM_WEEKLY(), locale.INLINE_REM_MONTHLY()],
        [locale.INLINE_REM_CUSTOM_REPEAT(), locale.INLINE_REM_CANCEL()]
    ]
    
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=action_map[text]) for text in row]
        for row in menu_layout
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def inline_reminders_last(locale):
    action_map = {
        locale.INLINE_REM_CONFIRM(): "remind_confirm",
        locale.INLINE_REM_CANCEL(): "back_remind"
    }
    
    menu_layout = [
        [locale.INLINE_REM_CONFIRM()],
        [locale.INLINE_REM_CANCEL()]
    ]
    
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=action_map[text]) for text in row]
        for row in menu_layout
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def inline_reminders_custom(locale):
    action_map = {
        locale.INLINE_CUSTOM_MINUTES(): "remind_minutes1",
        locale.INLINE_CUSTOM_HOURS(): "remind_hours1",
        locale.INLINE_CUSTOM_DAYS(): "remind_days1",
        locale.INLINE_CUSTOM_WEEKS(): "remind_weeks1",
        locale.INLINE_CUSTOM_MONTHLY(): "remind_monthly1",
        locale.INLINE_REM_CANCEL(): "back_remind"
    }
    
    menu_layout = [
        [locale.INLINE_CUSTOM_MINUTES()],
        [locale.INLINE_CUSTOM_HOURS(), locale.INLINE_CUSTOM_DAYS()],
        [locale.INLINE_CUSTOM_WEEKS(), locale.INLINE_CUSTOM_MONTHLY()],
        [locale.INLINE_REM_CANCEL()]
    ]
    
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=action_map[text]) for text in row]
        for row in menu_layout
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def inline_repeat_reminders_custom(locale):
    action_map = {
        locale.INLINE_CUSTOM_HOURS(): "remind_repeat_hours",
        locale.INLINE_CUSTOM_DAYS(): "remind_repeat_days",
        locale.INLINE_CUSTOM_WEEKS(): "remind_repeat_weeks",
        locale.INLINE_CUSTOM_MONTHLY(): "remind_repeat_monthly",
        locale.INLINE_REM_CANCEL(): "back_remind"
    }
    
    menu_layout = [
        [locale.INLINE_CUSTOM_HOURS(), locale.INLINE_CUSTOM_DAYS()],
        [locale.INLINE_CUSTOM_WEEKS(), locale.INLINE_CUSTOM_MONTHLY()],
        [locale.INLINE_REM_CANCEL()]
    ]
    
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=action_map[text]) for text in row]
        for row in menu_layout
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


class DeleteRemind(CallbackData, prefix = "delete_remind"):
    text: str

async def inline_delete_remind(locale, chat_id):

    keyboard = InlineKeyboardBuilder()
    messages = await db_nosql.get_delayed_messages(chat_id)
    for message in messages:
        keyboard.add(InlineKeyboardButton(text=message['message'], callback_data = DeleteRemind(text=str(message['message'])).pack()))
    keyboard.add(InlineKeyboardButton(text=locale.REPLY_BACK(), callback_data = "back_remind"))
    return keyboard.adjust(1, repeat=True).as_markup()




def inline_update_main_goal(locale):
    action_map = {
        locale.INLINE_EDIT_MAIN_GOAL(): "update_main_goal"
    }
    
    menu_layout = [
        [locale.INLINE_EDIT_MAIN_GOAL()]
    ]
    
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=action_map[text]) for text in row]
        for row in menu_layout
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


class FriendRequest(CallbackData, prefix = "friend_request"):
    chat_id: str
    username: str
    type: str

async def inline_friend_request(locale, requester, requster_username):

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=locale.INLINE_FRIEND_ACCEPT(), callback_data = FriendRequest(chat_id=str(requester), type='accept', username = requster_username).pack()))
    keyboard.add(InlineKeyboardButton(text=locale.INLINE_FRIEND_DECLINE(), callback_data = FriendRequest(chat_id=str(requester), type="decline", username = requster_username).pack()))
    return keyboard.adjust(2, repeat=True).as_markup()

async def inline_friends_stata(locale):
    action_map = {
        locale.INLINE_RAT_SHOW_FRIENDS(): "friends_stata"
    }
    
    menu_layout = [
        [locale.INLINE_RAT_SHOW_FRIENDS()]
    ]
    
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=action_map[text]) for text in row]
        for row in menu_layout
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def inline_update_notification(locale, now):
    print(now, "now")
    if now == True:
        result = 'ON'
    else:
        result = 'OFF'
    action_map = {
        locale.INLINE_NOTIFICATION(now = result): "notification_update"
    }
    
    menu_layout = [
        [locale.INLINE_NOTIFICATION(now = result)]
    ]
    
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=action_map[text]) for text in row]
        for row in menu_layout
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def reply_micro(locale):
    # Структура меню в виде списка строк
    menu_layout = [
        [locale.REPLY_MC_ACTIVE(), locale.REPLY_MC_CATALOG()],
        [locale.REPLY_MC_CREATE(), locale.REPLY_MC_TEMPLATES()],
        [locale.REPLY_MAIN()]
    ]
    
    # Преобразование в клавиатуру
    keyboard = [
        [KeyboardButton(text=text) for text in row]
        for row in menu_layout
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


async def reply_catalog(locale):
    # Структура меню в виде списка строк
    menu_layout = [
        [locale.REPLY_MAIN(), locale.REPLY_MC_CAT_PORN_ADDICTION()]
        
    ]
    
    # Преобразование в клавиатуру
    keyboard = [
        [KeyboardButton(text=text) for text in row]
        for row in menu_layout
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

class MicrochalangeRequest(CallbackData, prefix = "microchalange_request"):
    type: str

async def inline_microchalange_request(locale, type):

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=locale.INLINE_YES(), callback_data = MicrochalangeRequest(type=type).pack()))
    keyboard.add(InlineKeyboardButton(text=locale.INLINE_NO(), callback_data = "main"))
    return keyboard.adjust(2, repeat=True).as_markup()

async def inline_porn_video():

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="VIDEO", callback_data = "video", url='https://youtu.be/DfV8LuHZ6vI?si=PasAiQSXFQK2p4Hb'))
    return keyboard.adjust(1, repeat=True).as_markup()

async def inline_porn_video1():

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="VIDEO", callback_data = "video", url='https://youtu.be/FdZ9Xzjpo1s?si=Uk0CLgt-qFPNvsH6'))
    return keyboard.adjust(1, repeat=True).as_markup()


async def inline_check():
    return [
        [
            {"text": "Всё замечательно", "callback_data": "btn1"},
            {"text": "Было не легко", "callback_data": "btn2"},
            {"text": "Сорвалась", "callback_data": "btn3"}
        ]
    ]
    
    
async def inline_admin():

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Выдать премиум", callback_data = "set_premium"))
    return keyboard.adjust(1, repeat=True).as_markup()