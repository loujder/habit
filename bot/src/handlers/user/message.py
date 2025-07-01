from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message
from fluentogram import TranslatorRunner

from aiogram.types import ReplyKeyboardRemove

from shared.utils.db_nosql import rdb, Referrals, UserCache, UserFriends, UserMicroChallenge
from shared.utils.db_sql import async_session
from sqlalchemy import Column, Integer, String, DateTime, select
from shared.utils import db_nosql
import random
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from src.handlers.user import keyboards
from shared.models.user import User1
from sqlalchemy import select, func
from sqlalchemy.orm import aliased

async def get_top_users():
    async with async_session() as session:
        # Создаем подзапрос для вычисления суммы stars + awards
        subquery = (
            select(
                User1.id,
                (User1.stars + User1.awards).label("total_score")
            )
            .subquery()
        )
        
        # Алиас для корректного соединения
        user_alias = aliased(User1)
        
        # Основной запрос с сортировкой по сумме
        query = (
            select(user_alias)
            .join(subquery, user_alias.id == subquery.c.id)
            .order_by(subquery.c.total_score.desc())
            .limit(10)
        )
        
        result = await session.execute(query)
        top_users = result.scalars().all()
        return top_users



motivation_porn_messages = [
    "Каждый новый день — это новая возможность стать лучше, чем вчера. Как ты себя чувствуешь сегодня?",
    "Улыбнись сегодня — это лучший способ начать день с позитивом. Как ты себя чувствуешь сегодня?",
    "Достижения начинаются с веры в себя. Верь в свои силы! Как ты себя чувствуешь сегодня?",
    "Маленькие шаги ведут к большим победам. Как ты себя чувствуешь сегодня?",
    "Не бойся ошибок — они делают тебя сильнее и мудрее. Как ты себя чувствуешь сегодня?",
    "Сегодня — отличный день для новых начинаний. Как ты себя чувствуешь сегодня?",
    "Твоя настойчивость — ключ к успеху. Как ты себя чувствуешь сегодня?",
    "Пусть сегодня будет день, когда ты сделаешь что-то важное для себя. Как ты себя чувствуешь сегодня?",
    "Самое лучшее время для действий — сейчас. Как ты себя чувствуешь сегодня?",
    "Верить в себя — первый шаг к достижению целей. Как ты себя чувствуешь сегодня?",
    "Каждый день — шанс стать чуть лучше, чем вчера. Как ты себя чувствуешь сегодня?",
    "Не останавливайся на достигнутом, впереди еще много возможностей. Как ты себя чувствуешь сегодня?",
    "Позитивное мышление притягивает хорошие события. Как ты себя чувствуешь сегодня?",
    "Ты способен на большее, чем думаешь. Как ты себя чувствуешь сегодня?",
    "Начни свой день с благодарности и улыбки. Как ты себя чувствуешь сегодня?",
    "Твои мечты стоят того, чтобы за них бороться. Как ты себя чувствуешь сегодня?",
    "Самое важное — не то, сколько раз ты упал, а сколько раз поднялся. Как ты себя чувствуешь сегодня?",
    "Делай сегодня то, что другие не хотят, и завтра будешь там, где другие не смогут быть. Как ты себя чувствуешь сегодня?",
    "Верь в чудеса — они случаются с теми, кто верит в них. Как ты себя чувствуешь сегодня?",
    "Ты создаешь свою реальность своими мыслями и действиями. Как ты себя чувствуешь сегодня?"
]

work_messages = [
    "Эта функция скоро будет доступна! Спасибо за терпение.",
    "Работа над этой функцией продолжается. Скоро всё будет готово!",
    "Извините за неудобство, эта функция сейчас в разработке. Следите за обновлениями!",
    "Эта возможность пока недоступна, но мы работаем над её реализацией.",
    "Функция в процессе разработки. Вернёмся к вам чуть позже!",
    "Пока эта функция недоступна, но мы уже над ней работаем.",
    "Эта опция скоро появится! Благодарим за ваше терпение.",
    "Функция находится в стадии разработки. Оставайтесь с нами!"
]


class Reminders(StatesGroup):
    remind_add = State()
    remind_time = State()
    remind_when = State()
    remind_custom = State()
    remind_repeat_custom = State()
    remind_seconds = State()
    
class Targets(StatesGroup):
    new_target = State()

class Adminpanel(StatesGroup):
    set_premium = State()
    
router = Router()
@router.message(F.text == "МЕНЮ")
@router.message(Command('start'))
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_friends: UserFriends,
            user_microchalenges: UserMicroChallenge,
            user_referalls: Referrals
            ):
    await state.clear()
    async with async_session() as session:
        user = await session.scalar(select(User1).filter_by(chat_id=message.from_user.id))
        if not user:
            new_user = User1(
                chat_id = message.from_user.id,
                username = '@'+message.from_user.username,
            )
            session.add(new_user)
            await session.commit()
    
    stats = await user_cache.get_stats(message.from_user.id)
    await message.answer(text=str(locale.welcome_text(username=message.from_user.first_name,
            points=stats['stars'],
            awards=stats['awards'])), reply_markup=keyboards.main(locale))
    # Получаем все ключи по шаблону
    if len(str(message.text).split()) == 2:
        if len(str(message.text).split()[1].split("_")) == 2:
            print("friend")
            friend_id = int(str(message.text).split()[1].split("_")[1])
            print(friend_id)
            status = await user_friends.are_friends(int(message.from_user.id), friend_id)

            if status != True:
                async with async_session() as session:
                    user = await session.scalar(select(User1.username).filter_by(chat_id=friend_id))
                    
                await user_friends.add_friend_request(message.from_user.id, friend_id, user)
                
                await message.answer(locale.friens_request(username = user), reply_markup=await keyboards.inline_friend_request(locale, friend_id, user))
                await message.bot.send_message(friend_id, locale.friens_request_call(username = "@"+message.from_user.username))
        else:
            friend_id = int(str(message.text).split()[1])
            print("ref")
            await user_referalls.remove_referral(friend_id, message.from_user.id)
            if await user_referalls.is_referral_in_user_referrals(message.from_user.id, friend_id):
                print("В рефах")
            else:
                print("Не в рефах, добавляю")
                user_referalls1 = await user_referalls.count_referrals(friend_id)
                with async_session() as session:
                    user12 = await session.scalar(select(User1).filter_by(chat_id=friend_id))
                    if user12.status == 'user':
                        if (user_referalls1+1)%5 == 0:
                            
                            await user_cache.set_premium(friend_id, timedelta(days=7))
                await user_referalls.add_referral(int(friend_id), int(message.from_user.id))
        
@router.message(F.text == "ПРОФИЛЬ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.clear()
    stats = await user_cache.get_stats(message.from_user.id)
    status1 = await user_cache.get_status(message.from_user.id)
    print(stats['created_at'])
    if status1 == 'user':
        status = 'Freemium'
    else:
        status = 'Premium'
    await message.answer(locale.profile_menu_text(username = message.from_user.full_name, points=stats['stars'], awards_count = stats['awards'], registration_date = str(stats['created_at']).split('.')[0], status = status, target = stats['target']), reply_markup=await keyboards.reply_profile(locale))

@router.message(F.text == "ЦЕЛИ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.clear()
    stats = await user_cache.get_stats(message.from_user.id)
    await message.answer(locale.main_target(target = stats['target']), reply_markup=keyboards.inline_update_main_goal(locale))

@router.message(F.text == "ДРУЗЬЯ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            user_friends: UserFriends,
            state: FSMContext
            ):
    await state.clear()
    stats = await user_friends.get_friends(message.from_user.id)
    if len(stats) == 0:
        print(None)
        text = locale.friends_none()+f"<i>https://t.me/Habit_quest_bot?start=friend_{message.from_user.id}</i>"
    else:
        result = '\n'
        count = 1
        for friend in stats:
            result += str(count)+f". {friend[1]}\n"
            count+=1
        text = "🏋️Вот список твоих друзей"+result+f"\n<i>Для добавления друга попроси перейти его по ссылке - https://t.me/Habit_quest_bot?start=friend_{message.from_user.id}</i>" 
    
    await message.answer(text, reply_markup=await keyboards.inline_friends_stata(locale))
        



@router.message(F.text == "НАПОМИНАНИЯ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache
            ):
    delayed_messages = await db_nosql.get_delayed_messages(message.from_user.id)
    result = ''
    count = 1
    
    for message1 in delayed_messages:
        repeat = ''
        try:
            
            if message1['repeat']['interval_type'] == 'days':
                repeat=locale.remind_day(count=message1['repeat']['interval_value'])
            elif message1['repeat']['interval_type'] == 'weeks':
                repeat=locale.remind_weeks(count=message1['repeat']['interval_value'])
            elif message1['repeat']['interval_type'] == 'months':
                repeat=locale.remind_months(count=message1['repeat']['interval_value'])
            elif message1['repeat']['interval_type'] == 'hours':
                repeat=locale.remind_hours(count=message1['repeat']['interval_value'])
        except:
            repeat=locale.remind_once()
        result+=str(count)+'. '+locale.reminders_text(text = message1['message'], repeat = repeat)+'\n'
        count+=1
    await message.answer(text=str(locale.reminders_title(count = len(delayed_messages)))+"\n"+result, reply_markup=keyboards.reminders(locale))
    
    print(await db_nosql.get_delayed_messages(message.from_user.id))

@router.message(F.text == "УДАЛИТЬ НАПОМИНАНИЕ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    if len(await db_nosql.get_delayed_messages(message.from_user.id)) == 0:
        await message.answer(locale.error_remind())
    else:
        await message.answer(locale.remind_delete(), reply_markup=await keyboards.inline_delete_remind(locale, message.from_user.id))





@router.message(F.text == "ДОБАВИТЬ НОВОЕ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    count_reminders = len(await db_nosql.get_delayed_messages(message.from_user.id))
    status = await user_cache.get_status(message.from_user.id)
    if status == 'user' and count_reminders+1<=1:
        await state.set_state(Reminders.remind_add)
        await message.answer(text=str(locale.remind_add(count = 0)), reply_markup=ReplyKeyboardRemove())
    elif status == 'premium' and count_reminders+1 <= 3:
        await state.set_state(Reminders.remind_add)
        await message.answer(text=str(locale.remind_add(count = 0)), reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(locale.REMIND_LIMIT())
    
@router.message(Reminders.remind_add)
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.update_data(remind_add = message.text)
    await message.answer(text=str(locale.remind_ask_time(text = message.text)), reply_markup=keyboards.inline_reminders(locale))

@router.message(Reminders.remind_custom)
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    try:
        count = int(message.text)
        
        await state.update_data(remind_custom = count)
        await message.answer(text=str(locale.remind_type(time = message.text)), reply_markup=keyboards.inline_reminders_custom(locale))
    except:
        await message.answer(str(locale.error()))
        
        
@router.message(Reminders.remind_repeat_custom)
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    try:
        count = int(message.text)
        
        await state.update_data(remind_repeat_custom = count)
        await message.answer(text=str(locale.remind_repeat_type(time = message.text)), reply_markup=keyboards.inline_repeat_reminders_custom(locale))
    except:
        await message.answer(str(locale.error()))
        
        
        
@router.message(Targets.new_target)
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    goal = message.text
    await state.clear()
    await user_cache.update_stats(target=goal, user_id=message.from_user.id)
    await message.answer(locale.main_target(target = goal), reply_markup=keyboards.inline_update_main_goal(locale))
    
@router.message(F.text == "НАСТРОЙКИ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.clear()
    stata = await user_cache.get_stats(message.from_user.id)
    await message.answer(locale.settings(), reply_markup=await keyboards.inline_update_notification(locale, stata['notification']))

@router.message(Command('help'))
@router.message(F.text == "ПОМОЩЬ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.clear()
    await message.answer(locale.help_text())
    
@router.message(F.text == "МИКРОЧЕЛЛЕНДЖИ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.clear()
    await message.answer(locale.micro_text(), reply_markup=await keyboards.reply_micro(locale))
    
@router.message(F.text == "КАТАЛОГ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_microchalenges: UserMicroChallenge
            ):
    await state.clear()
    res = await user_microchalenges.get_challenge(message.from_user.id)
    if res == None:
        await message.answer(locale.CATALOG(), reply_markup=await keyboards.reply_catalog(locale))
    else:
        await message.answer(locale.error_micro())
        
@router.message(F.text == "АКТИВНЫЕ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_microchalenges: UserMicroChallenge
            ):
    
    await state.clear()
    res = await user_microchalenges.get_challenge(message.from_user.id)
    
    if res != None:
        start_date = res['start_date']
        end_date = start_date + timedelta(days=7)
        now = datetime.now()
        remaining_time = end_date - now
        remaining_days = remaining_time.days
        stage=''
        stage+="■"*res['personal_record']
        stage+="□"*(7-res['personal_record'])
        await message.answer(f"Ваш прогресс в челендже: [{stage}] - ({res['personal_record']} из 7 этапов выполнено)\n\nПродолжайте в том же духе — осталось немного до завершения!(до завершения осталось: {remaining_days} дней)\n\n<a href='https://youtu.be/FdZ9Xzjpo1s?si=Uk0CLgt-qFPNvsH6'>Посмотреть видео на эту тему</a>\n<a href='https://te.legra.ph/mikrochelendzh-po-izbavleniyu-ot-porno-zavisimosti-06-26'>Почитать статью об челендже</a>")    
    else:
        await message.answer(locale.error_active())
    
@router.message(F.text == "🧠Порнозависимость")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_microchalenges: UserMicroChallenge
            ):
    await state.clear()
    res = await user_microchalenges.get_challenge(message.from_user.id)
    if res == None:
        level = await user_microchalenges.get_level(message.from_user.id, 'porn')
        print(await user_microchalenges.get_level(message.from_user.id, "fitness"))
        data = await user_cache.get_stats(message.from_user.id)
        if data['status'] != 'user' or level==1:
            await message.answer(locale.MC_CAT_PORN_ADDICTION(username = message.from_user.full_name), reply_markup=await keyboards.inline_microchalange_request(locale, 'porn'))
        else:
            await message.answer(locale.error_level())
    else:
        await message.answer(locale.error_micro())
        
@router.message(F.text == "ПРЕМИУМ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_microchalenges: UserMicroChallenge
            ):
    await state.clear()
    data = await user_cache.get_stats(message.from_user.id)     
    if data['status'] == 'user':
        await message.answer(locale.NON_PREMIUM())
        
@router.message(F.text == "РЕФКА")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_microchalenges: UserMicroChallenge,
            user_referalls: Referrals
            ):
    await state.clear()
    await message.answer(locale.REFKA(ref = f'https://t.me/Habit_quest_bot?start={message.from_user.id}', refe=await user_referalls.count_referrals(message.from_user.id)))

@router.message(F.text == "РЕЙТИНГИ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.clear()
    result = await get_top_users()
    mes = "🔥 Топ-10 лучших пользователей по очкам и наградам: 🔥\n"
    count = 1
    for user in result:
        mes+=f"{count}. {user.username} — {user.stars} очков, {user.awards} наград\n"
        count+=1
    await message.answer(mes)
    
@router.message(Command('adminpanel'))
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_friends: UserFriends,
            user_microchalenges: UserMicroChallenge,
            user_referalls: Referrals
            ):
    await state.clear()
    status = await user_cache.get_stats(message.from_user.id)
    if status['status'] == 'admin':
        await message.answer(locale.ADMIN(), reply_markup=await keyboards.inline_admin())



@router.message(F.text == "МОИ ШАБЛОНЫ")
@router.message(F.text == "СОЗДАТЬ СВОЙ")
@router.message(F.text == "ГРУППЫ")
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_microchalenges: UserMicroChallenge
            ):
    await state.clear()
    await message.answer(random.choice(work_messages))
    
    
@router.message(Adminpanel.set_premium)
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    status = await user_cache.get_stats(message.from_user.id)
    if status['status'] == 'admin':
        mes = message.text
        
        try:
            await user_cache.set_premium(mes.split()[0], timedelta(days=mes.split()[1]))
            await message.answer("Удачно")
        except:
            await message.answer("Ошибка")
    await state.clear()