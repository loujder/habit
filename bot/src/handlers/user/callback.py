import random
from aiogram import Router, Bot, F
from aiogram.types import ReplyKeyboardRemove, CallbackQuery
from src.handlers.user import keyboards
from shared.utils.callbacks import Task
from shared.utils.db_nosql import rdb, UserFriends
from fluentogram import TranslatorRunner
from shared.utils.db_nosql import UserCache, UserMicroChallenge
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from shared.utils import db_nosql
import pytz
from src.handlers.user.message import Reminders, Targets, Adminpanel

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

daily_messages = [
    # День 1
    "<b>День 1: Анализ триггеров и осознанность</b>\n<i>Задача: Выявить контекст, запускающий тягу к порно.</i>\n\n<b>Действия:</b>\n1. Запишите 3 ситуации-триггера (пример: 'ночь', 'стресс', 'скука').\n2. Замените одну из них на активность, требующую фокуса (10 мин. дыхательных упражнений, холодный душ).\n\n<b>Научная основа:</b> Осознание триггеров снижает автоматизм зависимого поведения на 47% (Journal of Behavioral Addictions, 2021).\n\nКак прошел твой предыдущий день?",
    
    # День 2
    "<b>День 2: Деконструкция ритуала</b>\n<i>Задача: Разорвать цепочку 'импульс → порно → мастурбация'.</i>\n\n<b>Действия:</b>\n1. При импульсе выждите 15 мин., займив руки (пазл, лепка).\n2. Мастурбация разрешена только после паузы без стимулов (никаких образов/видео).\n\n<b>Научная основа:</b> 15-минутная задержка ослабляет силу привычки на 32% (Psychology of Consciousness, 2022).\n\nКак прошел твой предыдущий день?",
    
    # День 3
    "<b>День 3: Замещение дофаминовых источников</b>\n<i>Задача: Перенаправить потребность в стимуляции.</i>\n\n<b>Действия:</b>\n1. При тяге выполните 20 мин. интенсивной нагрузки (приседания, бёрпи).\n2. После мастурбации (без порно!) сразу займитесь творчеством (рисование, музыка).\n\n<b>Научная основа:</b> Физнагрузка повышает естественный дофамин на 40% (Neuropharmacology, 2023).\n\nКак прошел твой предыдущий день?",
    
    # День 4
    "<b>День 4: Цифровая гигиена</b>\n<i>Задача: Устранить лёгкий доступ к контенту.</i>\n\n<b>Действия:</b>\n1. Удалите приложения с доступом к порно, установите BlockSite.\n2. Включите фильтры NSFW в настройках ОС.\n3. Уберите гаджеты из спальни на ночь.\n\n<b>Научная основа:</b> 80% срывов происходят из-за отсутствия барьеров (Cyberpsychology, 2020).\n\nКак прошел твой предыдущий день?",
    
    # День 5
    "<b>День 5: Перезагрузка лимбической системы</b>\n<i>Задача: Снизить реакцию мозга на триггеры.</i>\n\n<b>Действия:</b>\n1. При мыслях о порно 5 мин. смотрите на природу (дерево, видео океана).\n2. Используйте ASMR-аудио (дождь, шепот) для переключения.\n\n<b>Научная основа:</b> Природные стимулы снижают активность миндалевидного тела на 27% (Frontiers in Human Neuroscience, 2022).\n\nКак прошел твой предыдущий день?",
    
    # День 6
    "<b>День 6: Социальная ответственность</b>\n<i>Задача: Создать внешнюю поддержку.</i>\n\n<b>Действия:</b>\n1. Поделитесь целью с доверенным лицом ('Я не смотрю порно 30 дней').\n2. При срыве сразу обсудите причины.\n\n<b>Научная основа:</b> Наличие 'партнёра по ответственности' повышает успех в 3 раза (Journal of Clinical Psychology, 2023).\n\nКак прошел твой предыдущий день?",
    
    # День 7
    "<b>День 7: Интеграция паттернов</b>\n<i>Задача: Закрепить новые привычки.</i>\n\n<b>Действия:</b>\n1. Составьте чек-лист 'Антикризисных мер' (пример: 'Тяга → 50 отжиманий → звонок другу').\n2. Удалите все закладки/историю, связанные с порно.\n\n<b>Научная основа:</b> Ритуалы замены формируют устойчивые нейронные связи за 21 день (Nature Human Behaviour, 2021).\n\nКак прошел твой предыдущий день?"
]

daily_message_premium = [
    # Неделя 2 (Углубленная работа с триггерами)
    "<b>День 8: Аудит триггерных сред</b>\n<i>Задача: Выявить скрытые триггеры в окружении.</i>\n\n<b>Действия:</b>\n1. Просканируйте 3 места (рабочий стол, соцсети, маршруты)\n2. Устраните 1 скрытый триггер (напр. «Инстаграм → удалить провокационные аккаунты»)\n\n<b>Наука:</b> 68% рецидивов вызваны неучтенными триггерами (Cyberpsychology, 2023)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 9: Техника «Замороженный образ»</b>\n<i>Задача: Ослабить эмоциональный отклик на образы.</i>\n\n<b>Действия:</b>\n1. При флешбэке представьте картинку в черно-белом цвете\n2. Медленно «заморозьте» и расколите льдинку\n\n<b>Наука:</b> Визуальное искажение снижает возбуждение миндалевидного тела на 41% (Journal of Neuroscience, 2022)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 10: Дофаминовое картографирование</b>\n<i>Задача: Создать альтернативные источники радости.</i>\n\n<b>Действия:</b>\n1. Составьте список из 5 «здоровых дофаминовых ударов» (напр. скалолазание)\n2. Реализуйте 1 пункт сегодня\n\n<b>Наука:</b> Новые хобби формируют конкурентные нейронные пути за 72 часа (Nature, 2023)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 11: Цифровой детокс 2.0</b>\n<i>Задача: Перестроить отношения с технологиями.</i>\n\n<b>Действия:</b>\n1. Включите монохромный режим экрана\n2. Удалите все приложения для анонимного просмотра\n\n<b>Наука:</b> Отсутствие цвета снижает стимулирующий эффект контента на 57% (ACM CHI, 2024)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 12: Соматическая синхронизация</b>\n<i>Задача: Восстановить связь с телом.</i>\n\n<b>Действия:</b>\n1. 15 мин. скан-медитации (поочередное напряжение/расслабление мышц)\n2. Мастурбация только после процедуры\n\n<b>Наука:</b> Телесная осознанность снижает компульсивность на 63% (Body Image, 2023)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 13: Когнитивное реструктурирование</b>\n<i>Задача: Изменить нарратив зависимости.</i>\n\n<b>Действия:</b>\n1. Напишите письмо себе от лица «здорового Я»\n2. Опишите 3 конкретных преимущества свободы\n\n<b>Наука:</b> Самоперсонализация укрепляет префронтальную кору (Frontiers in Psychology, 2023)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 14: Рефрейминг сексуальности</b>\n<i>Задача: Отделить физиологию от цифровых паттернов.</i>\n\n<b>Действия:</b>\n1. Читайте научную литературу о сексуальном здоровье\n2. Практикуйте мастурбацию с завязанными глазами\n\n<b>Наука:</b> Тактильная фокусировка перестраивает сенсорные карты за 14 дней (The Journal of Sexual Medicine, 2023)\n\nКак прошел твой предыдущий день?",

    # Неделя 3 (Формирование новой идентичности)
    "<b>День 15: Ритуал «Сжигание мостов»</b>\n<i>Задача: Создать точку невозврата.</i>\n\n<b>Действия:</b>\n1. Уничтожьте носители с контентом (флешки, архивные папки)\n2. Совершите символический акт обновления\n\n<b>Наука:</b> Ритуалы дают мозгу сигнал о необратимости изменений (Neuron, 2023)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 16: Нейробика желаний</b>\n<i>Задача: Перепрограммировать систему вознаграждения.</i>\n\n<b>Действия:</b>\n1. При тяге 10 мин. играйте на музыкальном инструменте\n2. Чередуйте холодные/горячие стимулы (лед в руку → чай)\n\n<b>Наука:</b> Конкурирующие сенсорные сигналы блокируют дофаминовые импульсы (Science Advances, 2024)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 17: Социальная реинтеграция</b>\n<i>Задача: Восстановить офлайн-связи.</i>\n\n<b>Действия:</b>\n1. Инициируйте 2 встречи с друзьями без гаджетов\n2. Обсуждайте только позитивные темы\n\n<b>Наука:</b> Офлайн-коммуникация повышает окситоцин на 32% (Psychoneuroendocrinology, 2023)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 18: Контракт с будущим</b>\n<i>Задача: Закрепить долгосрочные обязательства.</i>\n\n<b>Действия:</b>\n1. Подпишите договор с собой с конкретными санкциями\n2. Включите пункт о благотворительности при срыве\n\n<b>Наука:</b> Письменные обязательства повышают compliance на 89% (Journal of Applied Psychology, 2023)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 19: Ценностно-ориентированное планирование</b>\n<i>Задача: Связать воздержание с жизненными целями.</i>\n\n<b>Действия:</b>\n1. Нарисуйте «колесо баланса» с 8 сферами жизни\n2. Отметьте, как порно мешает каждой сфере\n\n<b>Наука:</b> Видение будущего снижает импульсивность на 77% (Personality and Individual Differences, 2023)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 20: Терапия отвращением</b>\n<i>Задача: Создать отрицательные ассоциации.</i>\n\n<b>Действия:</b>\n1. При фантазиях включайте неприятный звук (напр. вилка по стеклу)\n2. Смотрите документации о вреде индустрии\n\n<b>Наука:</b> Негативное подкрепление изменяет условные рефлексы за 48 часов (Behavioural Brain Research, 2023)\n\nКак прошел твой предыдущий день?",
    
    "<b>День 21: Церемония перехода</b>\n<i>Задача: Закрепить новую идентичность.</i>\n\n<b>Действия:</b>\n1. Создайте физический артефакт «нового Я» (кулон, кольцо)\n2. Публично объявите о личной победе\n\n<b>Наука:</b> Символические переходы активируют систему самоидентификации (NeuroImage, 2024)\n\nКак прошел твой предыдущий день?"
]

router = Router()

@router.callback_query(F.data == "back_remind")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.clear()
    await callback.message.delete()
    delayed_messages = await db_nosql.get_delayed_messages(callback.from_user.id)
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
        except:
            repeat=locale.remind_once()
        result+=str(count)+'. '+locale.reminders_text(text = message1['message'], repeat = repeat)+'\n'
        count+=1
    await callback.message.answer(text=str(locale.reminders_title(count = len(delayed_messages)))+"\n"+result, reply_markup=keyboards.reminders(locale))
    

    
    
@router.callback_query(keyboards.DeleteRemind.filter())
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            callback_data: keyboards.DeleteRemind
            ):
    await db_nosql.delete_delayed_message(callback.from_user.id, callback_data.text)
    if len(await db_nosql.get_delayed_messages(callback.from_user.id)) == 0:
        await callback.message.edit_text(locale.error_remind())
    else:
        await callback.message.edit_text(locale.remind_delete(), reply_markup=await keyboards.inline_delete_remind(locale, callback.from_user.id))


@router.callback_query(F.data == "remind_30")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    await state.update_data(remind_time = "30 minutes")
    await callback.message.edit_text(locale.remind_confirm(text = data['remind_add'], time = 'через 30 минут'), reply_markup=keyboards.inline_reminders_when(locale))


@router.callback_query(F.data == "remind_60")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    await state.update_data(remind_time = "60 minutes")
    await callback.message.edit_text(locale.remind_confirm(text = data['remind_add'], time = 'через 1 час'), reply_markup=keyboards.inline_reminders_when(locale))

@router.callback_query(F.data == "remind_120")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    await state.update_data(remind_time = "120 minutes")
    await callback.message.edit_text(locale.remind_confirm(text = data['remind_add'], time = 'через 2 часа'), reply_markup=keyboards.inline_reminders_when(locale))


@router.callback_query(F.data == "remind_custom")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.set_state(Reminders.remind_custom)
    await callback.message.edit_text(locale.remind_custom())


@router.callback_query(F.data == "remind_minutes1")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    if int(data['remind_custom']) >= 5 and int(data['remind_custom']) <=120:
        await state.update_data(remind_time = str(data['remind_custom'])+f" minutes")
        await callback.message.edit_text(locale.remind_confirm(text = data['remind_add'], time = f"через {data['remind_custom']} минут"), reply_markup=keyboards.inline_reminders_when(locale))
    else:
        await callback.message.edit_text(locale.remind_error_minutes())

@router.callback_query(F.data == "remind_hours1")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    if int(data['remind_custom']) >= 1 and int(data['remind_custom']) <=50:
        await state.update_data(remind_time = str(data['remind_custom'])+f" hours")
        await callback.message.edit_text(locale.remind_confirm(text = data['remind_add'], time = f"через {data['remind_custom']} часов"), reply_markup=keyboards.inline_reminders_when(locale))
    else:
        await callback.message.edit_text(locale.remind_error_hours())
@router.callback_query(F.data == "remind_days1")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    if int(data['remind_custom']) >= 1 and int(data['remind_custom']) <=50:
        await state.update_data(remind_time = str(data['remind_custom'])+f" days")
        await callback.message.edit_text(locale.remind_confirm(text = data['remind_add'], time = f"через {data['remind_custom']} дней"), reply_markup=keyboards.inline_reminders_when(locale))
    else:
        await callback.message.edit_text(locale.remind_error_days())
@router.callback_query(F.data == "remind_weeks1")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    if int(data['remind_custom']) >= 1 and int(data['remind_custom']) <=5:
        await state.update_data(remind_time = str(data['remind_custom'])+f" weeks")
        await callback.message.edit_text(locale.remind_confirm(text = data['remind_add'], time = f"через {data['remind_custom']} недель"), reply_markup=keyboards.inline_reminders_when(locale))
    else:
        await callback.message.edit_text(locale.remind_error_weeks())
@router.callback_query(F.data == "remind_monthly1")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    if int(data['remind_custom']) >= 1 and int(data['remind_custom']) <=2:
        await state.update_data(remind_time = str(data['remind_custom'])+f" monthly")
        await callback.message.edit_text(locale.remind_confirm(text = data['remind_add'], time = f"через {data['remind_custom']} месяцев"), reply_markup=keyboards.inline_reminders_when(locale))
    else:
        await callback.message.edit_text(locale.remind_error_months())
@router.callback_query(F.data == "remind_repeat_custom")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.set_state(Reminders.remind_repeat_custom)
    await callback.message.edit_text(text=locale.remind_repeat_custom())



@router.callback_query(F.data == "remind_once")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    await state.update_data(remind_when = 'once')
    moscow_tz = pytz.timezone('Europe/Moscow')
    if str(data['remind_time']).split()[1] == 'minutes':
        time = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0]))).split(".")[0]
    elif str(data['remind_time']).split()[1] == 'seconds':
        time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
    elif str(data['remind_time']).split()[1] == 'hours':
        time = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0]))).split(".")[0]
    elif str(data['remind_time']).split()[1] == 'days':
        time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0]))).split(".")[0]
    elif str(data['remind_time']).split()[1] == 'weeks':
        time = str(datetime.now(moscow_tz) + timedelta(weeks=int(str(data['remind_time']).split()[0]))).split(".")[0]
    elif str(data['remind_time']).split()[1] == 'monthly':
        time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30)).split(".")[0]
    await callback.message.edit_text(locale.remind_last(text = data['remind_add'], first = str(time), time='один раз в '+str(time)), reply_markup=keyboards.inline_reminders_last(locale))

@router.callback_query(F.data == "remind_daily")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    print("remind_daily")
    data = await state.get_data()
    await state.update_data(remind_when = 'days')
    moscow_tz = pytz.timezone('Europe/Moscow')
    if str(data['remind_time']).split()[1] == 'minutes':
        time = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0])) + timedelta(days=1)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'seconds':
        time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0])) + timedelta(days=1)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'hours':
        time = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0])) + timedelta(days=1)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'days':
        time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])) + timedelta(days=1)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'weeks':
        time = str(datetime.now(moscow_tz) + timedelta(weeks=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*7) + timedelta(days=1)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'monthly':
        time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30)).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30) + timedelta(days=1)).split(".")[0]
    await state.update_data(remind_repeat_custom = 1)
    await callback.message.edit_text(locale.remind_last(text = data['remind_add'], first = str(time), time=str(repeat)), reply_markup=keyboards.inline_reminders_last(locale))



@router.callback_query(F.data == "remind_weekly")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    await state.update_data(remind_when = 'weekly')
    moscow_tz = pytz.timezone('Europe/Moscow')
    if str(data['remind_time']).split()[1] == 'minutes':
        time = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0])) + timedelta(days=7)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'seconds':
        time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0])) + timedelta(days=7)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'hours':
        time = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0])) + timedelta(days=7)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'days':
        time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])) + timedelta(days=7)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'weeks':
        time = str(datetime.now(moscow_tz) + timedelta(weeks=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*7) + timedelta(days=7)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'monthly':
        time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30)).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30) + timedelta(days=7)).split(".")[0]
    await state.update_data(remind_repeat_custom = 1)
    await callback.message.edit_text(locale.remind_last(text = data['remind_add'], first = str(time), time=str(repeat)), reply_markup=keyboards.inline_reminders_last(locale))

@router.callback_query(F.data == "remind_monthly")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    await state.update_data(remind_when = 'monthly')
    moscow_tz = pytz.timezone('Europe/Moscow')
    if str(data['remind_time']).split()[1] == 'minutes':
        time = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0])) + timedelta(days=30)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'seconds':
        time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0])) + timedelta(days=30)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'hours':
        time = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0])) + timedelta(days=30)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'days':
        time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])) + timedelta(days=30)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'weeks':
        time = str(datetime.now(moscow_tz) + timedelta(weeks=int(str(data['remind_time']).split()[0]))).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*7) + timedelta(days=30)).split(".")[0]

    elif str(data['remind_time']).split()[1] == 'monthly':
        time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30)).split(".")[0]
        repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30) + timedelta(days=30)).split(".")[0]
    await state.update_data(remind_repeat_custom = 1)
    await callback.message.edit_text(locale.remind_last(text = data['remind_add'], first = str(time), time=str(repeat)), reply_markup=keyboards.inline_reminders_last(locale))





    
    

@router.callback_query(F.data == "remind_repeat_hours")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    if int(data['remind_custom']) >= 1 and int(data['remind_custom']) <=50:
        await state.update_data(remind_when = 'hours')
        moscow_tz = pytz.timezone('Europe/Moscow')
        if str(data['remind_time']).split()[1] == 'minutes':
            time = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0])) + timedelta(hours=int(data['remind_repeat_custom']))).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'seconds':
            time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0])) + timedelta(hours=int(data['remind_repeat_custom']))).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'hours':
            time = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0])) + timedelta(hours=int(data['remind_repeat_custom']))).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'days':
            time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])) + timedelta(hours=int(data['remind_repeat_custom']))).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'weeks':
            time = str(datetime.now(moscow_tz) + timedelta(weeks=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*7) + timedelta(hours=int(data['remind_repeat_custom']))).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'monthly':
            time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30)).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30) + timedelta(hours=int(data['remind_repeat_custom']))).split(".")[0]
        await callback.message.edit_text(locale.remind_last(text = data['remind_add'], first = str(time), time=str(repeat)), reply_markup=keyboards.inline_reminders_last(locale))
    else:
        await callback.message.edit_text(locale.remind_error_hours())


@router.callback_query(F.data == "remind_repeat_days")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    if int(data['remind_custom']) >= 1 and int(data['remind_custom']) <=50:
        await state.update_data(remind_when = 'days')
        moscow_tz = pytz.timezone('Europe/Moscow')
        if str(data['remind_time']).split()[1] == 'minutes':
            time = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom']))).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'seconds':
            time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom']))).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'hours':
            time = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom']))).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'days':
            time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom']))).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'weeks':
            time = str(datetime.now(moscow_tz) + timedelta(weeks=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*7) + timedelta(days=int(data['remind_repeat_custom']))).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'monthly':
            time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30)).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30) + timedelta(days=int(data['remind_repeat_custom']))).split(".")[0]
        await callback.message.edit_text(locale.remind_last(text = data['remind_add'], first = str(time), time=str(repeat)), reply_markup=keyboards.inline_reminders_last(locale))
    else:
        await callback.message.edit_text(locale.remind_error_days())
@router.callback_query(F.data == "remind_repeat_weeks")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    if int(data['remind_custom']) >= 1 and int(data['remind_custom']) <=5:
        await state.update_data(remind_when = 'weeks')
        moscow_tz = pytz.timezone('Europe/Moscow')
        if str(data['remind_time']).split()[1] == 'minutes':
            time = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom'])*7)).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'seconds':
            time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom'])*7)).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'hours':
            time = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom'])*7)).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'days':
            time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom'])*7)).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'weeks':
            time = str(datetime.now(moscow_tz) + timedelta(weeks=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*7) + timedelta(days=int(data['remind_repeat_custom'])*7)).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'monthly':
            time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30)).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30) + timedelta(days=int(data['remind_repeat_custom'])*7)).split(".")[0]
        await callback.message.edit_text(locale.remind_last(text = data['remind_add'], first = str(time), time=str(repeat)), reply_markup=keyboards.inline_reminders_last(locale))
    else:
        await callback.message.edit_text(locale.remind_error_weeks())

@router.callback_query(F.data == "remind_repeat_monthly")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    data = await state.get_data()
    if int(data['remind_custom']) >= 1 and int(data['remind_custom']) <=2:
        await state.update_data(remind_when = 'monthly')
        moscow_tz = pytz.timezone('Europe/Moscow')
        if str(data['remind_time']).split()[1] == 'minutes':
            time = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom'])*30)).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'seconds':
            time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom'])*30)).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'hours':
            time = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(hours=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom'])*30)).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'days':
            time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])) + timedelta(days=int(data['remind_repeat_custom'])*30)).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'weeks':
            time = str(datetime.now(moscow_tz) + timedelta(weeks=int(str(data['remind_time']).split()[0]))).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*7) + timedelta(days=int(data['remind_repeat_custom'])*30)).split(".")[0]

        elif str(data['remind_time']).split()[1] == 'monthly':
            time = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30)).split(".")[0]
            repeat = str(datetime.now(moscow_tz) + timedelta(days=int(str(data['remind_time']).split()[0])*30) + timedelta(days=int(data['remind_repeat_custom'])*30)).split(".")[0]
        await callback.message.edit_text(locale.remind_last(text = data['remind_add'], first = str(time), time=str(repeat)), reply_markup=keyboards.inline_reminders_last(locale))
    else:
        await callback.message.edit_text(locale.remind_error_months())



@router.callback_query(F.data == "remind_confirm")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await callback.message.delete()
    await user_cache.update_stats(callback.from_user.id, 5)
    data = await state.get_data()
    print(data)
    moscow_tz = pytz.timezone('Europe/Moscow')
    if str(data['remind_time']).split()[1] == 'minutes':
        time = str(datetime.now(moscow_tz) + timedelta(minutes=int(str(data['remind_time']).split()[0]))).split(".")[0]
        seconds = int(str(data['remind_time']).split()[0])*60
        print(seconds)
    elif str(data['remind_time']).split()[1] == 'seconds':
        time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
        seconds = int(str(data['remind_time']).split()[0])
        print(seconds)
    elif str(data['remind_time']).split()[1] == 'hours':
        time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
        seconds = int(str(data['remind_time']).split()[0])*60*60
    elif str(data['remind_time']).split()[1] == 'days':
        time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
        seconds = int(str(data['remind_time']).split()[0])*24*60*60
        print(seconds)
    elif str(data['remind_time']).split()[1] == 'weeks':
        time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
        seconds = int(str(data['remind_time']).split()[0])*7*24*60*60
    elif str(data['remind_time']).split()[1] == 'monthly':
        time = str(datetime.now(moscow_tz) + timedelta(seconds=int(str(data['remind_time']).split()[0]))).split(".")[0]
        seconds = int(str(data['remind_time']).split()[0])*30*24*60*60
    await callback.message.answer(text = str(locale.remind_create(time='в '+str(time))), reply_markup=keyboards.main(locale))
    

    if data['remind_when'] == 'once':
        await db_nosql.schedule_message(
        chat_id=callback.from_user.id,
        message=data['remind_add'],
        delay = seconds
        )
    elif data['remind_when'] == 'hours':
        await db_nosql.schedule_message(
        chat_id=callback.from_user.id,
        message=data['remind_add'],
        delay = seconds,
        repeat={
                "interval_type": data['remind_when'],
                "interval_value": data['remind_repeat_custom']
        }
        )
    elif data['remind_when'] == 'days':
        await db_nosql.schedule_message(
        chat_id=callback.from_user.id,
        message=data['remind_add'],
        delay = seconds,
        repeat={
                "interval_type": data['remind_when'],
                "interval_value": data['remind_repeat_custom']
        }
        )
    elif data['remind_when'] == 'weeks':
        await db_nosql.schedule_message(
        chat_id=callback.from_user.id,
        message=data['remind_add'],
        delay = seconds,
        repeat={
                "interval_type": data['remind_when'],
                "interval_value": data['remind_repeat_custom']
        }
        )
    elif data['remind_when'] == 'monthly':
        await db_nosql.schedule_message(
        chat_id=callback.from_user.id,
        message=data['remind_add'],
        delay = seconds,
        repeat={
                "interval_type": "months",
                "interval_value": data['remind_repeat_custom']
        }
        )
    await state.clear()
    
    
    
@router.callback_query(F.data == "update_main_goal")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext
            ):
    await state.clear()
    await callback.message.delete()
    await state.set_state(Targets.new_target)
    await callback.message.answer(locale.update_goal())
    
    
@router.callback_query(keyboards.FriendRequest.filter())
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            user_friends: UserFriends,
            state: FSMContext,
            callback_data: keyboards.FriendRequest
            ):
    await callback.message.delete()
    print(callback.from_user.id, "lllll")
    if callback_data.type == 'accept':
        await user_friends.add_friend(callback.from_user.id, (int(callback_data.chat_id), callback_data.username), (int(callback.from_user.id), "@"+callback.from_user.username))
        await user_friends.remove_friend_request(int(callback.from_user.id), int(callback_data.chat_id))
        await callback.message.answer(locale.friens_request_accept1())
        
        await callback.bot.send_message(text=locale.friens_request_accept(username = "@"+callback.from_user.username), chat_id=callback_data.chat_id)
    
    else:
        await user_friends.remove_friend_request(callback.from_user.id, callback_data.chat_id)
        

@router.callback_query(F.data == "friends_stata")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_friends: UserFriends
            ):
    await state.clear()
    await callback.message.delete()
    stata = await user_friends.get_friends_details(callback.from_user.id, user_cache)
    print(stata)
    text = '\n'
    for friend in stata:
        if friend['status'] == 'user':
            status = 'Freemium'
        text += "⬇️"+friend['user_id'][1]+"⬇️"+f"\n<blockquote expandable>{locale.friends_none_menu_text(points = friend['stars'], awards_count = friend['awards'], status = status, registration_date = friend['date'], target = friend['target'])}</blockquote>"
    await callback.message.answer('🏋️Вот список твоих друзей'+text)
    
@router.callback_query(F.data == "notification_update")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_friends: UserFriends
            ):
    await state.clear()
    stata = await user_cache.get_stats(callback.from_user.id)
    print(stata['notification'], "stata")
    if stata['notification'] == True:
        new_stata = False
    else:
        new_stata = True
    print(new_stata, "new stata")
    await user_cache.update_stats(callback.from_user.id, notification=new_stata)
    
    await callback.message.edit_text(locale.settings(), reply_markup=await keyboards.inline_update_notification(locale, new_stata))
    
    
@router.callback_query(keyboards.MicrochalangeRequest.filter())
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            user_friends: UserFriends,
            state: FSMContext,
            callback_data: keyboards.FriendRequest,
            user_microchalenges: UserMicroChallenge
            ):
    await callback.message.delete()
    await user_microchalenges.create_or_update_challenge(callback.from_user.id, callback_data.type)
    level1 = await user_microchalenges.get_level(callback.from_user.id, 'porn')
    if level1 == 1:
        await callback.message.answer(locale.NOTIFICATION_PORN_ADDICTION(), reply_markup=await keyboards.inline_porn_video1())
    else:
        await callback.message.answer(locale.NOTIFICATION_PORN_ADDICTION_PREMIUM(), reply_markup=await keyboards.inline_porn_video1())
    moscow_tz = pytz.timezone('Europe/Moscow')

    # Текущее время в Москве
    now = datetime.now(moscow_tz)

    # Создаем объект для сегодняшнего 12:00
    today_12 = now.replace(hour=12, minute=0, second=0, microsecond=0)

    # Если сейчас уже после 12:00, считаем до завтра в 12:00
    if now >= today_12:
        target_time = today_12 + timedelta(days=1)
    else:
        target_time = today_12

    # Вычисляем разницу в секундах
    seconds_until = int((target_time - now).total_seconds())
    print(f"Секунд до ближайшего 12:00 по Москве: {seconds_until}")
    level = await user_microchalenges.get_challenge(callback.from_user.id)
    if level1 == 1:
        await db_nosql.schedule_message(callback.from_user.id, daily_messages[int(level['personal_record'])], 10, await keyboards.inline_check(), hide=True)
    else:
        await db_nosql.schedule_message(callback.from_user.id, daily_message_premium[int(level['personal_record'])], 10, await keyboards.inline_check(), hide=True)

    
@router.callback_query(F.data == "btn1")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_microchalenges: UserMicroChallenge
            ):
    await state.clear()
    await callback.message.delete()
    res = await user_microchalenges.get_challenge(callback.from_user.id)
    if res != None:
        moscow_tz = pytz.timezone('Europe/Moscow')
        # Текущее время в Москве
        now = datetime.now(moscow_tz)

        # Создаем объект для сегодняшнего 19:00
        today_19 = now.replace(hour=19, minute=0, second=0, microsecond=0)

        # Если сейчас уже после 19:00, считаем до завтра в 19:00
        if now >= today_19:
            target_time = today_19 + timedelta(days=1)
        else:
            target_time = today_19
        level1 = await user_microchalenges.get_level(callback.from_user.id, 'porn')
        # Вычисляем разницу в секундах
        seconds_until = int((target_time - now).total_seconds())
        print(f"Секунд до ближайшего 19:00 по Москве: {seconds_until}")
        if level1 == 1:
            if int(res['personal_record']) <= 5:
                await db_nosql.schedule_message(callback.from_user.id, daily_messages[int(res['personal_record'])+1], 5, await keyboards.inline_check(), hide=True)
            else:
                stats = await user_cache.get_stats(callback.from_user.id)
                print(stats)
                if stats['status'] == 'user':
                    await db_nosql.schedule_message(callback.from_user.id, f"Поздравляю, челендж завершен!\n\n<i>К сожалению для повышения уровня челенджа требуется премиум</i>", 10, hide=True)

                else:
                    await db_nosql.schedule_message(callback.from_user.id, f"Поздравляю, челендж завершен!\n\n<i>Уровень челенджа можно повысить в каталоге, удачи, я верю в тебя</i>", 10, hide=True)

                await user_cache.update_stats(callback.from_user.id, awards_delta=15)
                await user_microchalenges.increase_level(callback.from_user.id)
                await user_microchalenges.delete_challenge(callback.from_user.id)
        else:
            if int(res['personal_record']) <= 12:
                await db_nosql.schedule_message(callback.from_user.id, daily_message_premium[int(res['personal_record'])+1], 5, await keyboards.inline_check(), hide=True)
            else:
                stats = await user_cache.get_stats(callback.from_user.id)
                print(stats)
                await db_nosql.schedule_message(callback.from_user.id, f"Поздравляю, челендж завершен!\n\n<i>К сожалению повышение уровня недоступно, мы ведем работу над новым курсом!</i>", 10, hide=True)


                await user_cache.update_stats(callback.from_user.id, awards_delta=15)
                await user_microchalenges.increase_level(callback.from_user.id)
                await user_microchalenges.delete_challenge(callback.from_user.id)
        await user_microchalenges.update_personal_record(callback.from_user.id)
        await user_microchalenges.update_last_response(callback.from_user.id)
        await callback.message.answer("Рад это слышать. Желаю тебе хорошего дня.", reply_markup=keyboards.main(locale))
        
        
    else:
        await callback.message.answer(locale.error())
        
        
@router.callback_query(F.data == "btn2")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_microchalenges: UserMicroChallenge
            ):
    await state.clear()
    await callback.message.delete()
    res = await user_microchalenges.get_challenge(callback.from_user.id)
    if res != None:
        moscow_tz = pytz.timezone('Europe/Moscow')
        # Текущее время в Москве
        now = datetime.now(moscow_tz)

        # Создаем объект для сегодняшнего 19:00
        today_19 = now.replace(hour=19, minute=0, second=0, microsecond=0)

        # Если сейчас уже после 19:00, считаем до завтра в 19:00
        if now >= today_19:
            target_time = today_19 + timedelta(days=1)
        else:
            target_time = today_19
        level1 = await user_microchalenges.get_level(callback.from_user.id, 'porn')
        # Вычисляем разницу в секундах
        seconds_until = int((target_time - now).total_seconds())
        print(f"Секунд до ближайшего 19:00 по Москве: {seconds_until}")
        if level1 == 1:
            if int(res['personal_record']) <= 5:
                await db_nosql.schedule_message(callback.from_user.id, daily_messages[int(res['personal_record'])+1], 5, await keyboards.inline_check(), hide=True)
            else:
                stats = await user_cache.get_stats(callback.from_user.id)
                print(stats)
                if stats['status'] == 'user':
                    await db_nosql.schedule_message(callback.from_user.id, f"Поздравляю, челендж завершен!\n\n<i>К сожалению для повышения уровня челенджа требуется премиум</i>", 10, hide=True)

                else:
                    await db_nosql.schedule_message(callback.from_user.id, f"Поздравляю, челендж завершен!\n\n<i>Уровень челенджа можно повысить в каталоге, удачи, я верю в тебя</i>", 10, hide=True)

                await user_cache.update_stats(callback.from_user.id, awards_delta=15)
                await user_microchalenges.increase_level(callback.from_user.id)
                await user_microchalenges.delete_challenge(callback.from_user.id)
        else:
            if int(res['personal_record']) <= 11:
                await db_nosql.schedule_message(callback.from_user.id, daily_message_premium[int(res['personal_record'])+1], 5, await keyboards.inline_check(), hide=True)
            else:
                stats = await user_cache.get_stats(callback.from_user.id)
                print(stats)
                await db_nosql.schedule_message(callback.from_user.id, f"Поздравляю, челендж завершен!\n\n<i>К сожалению повышение уровня недоступно, мы ведем работу над новым курсом!</i>", 10, hide=True)


                await user_cache.update_stats(callback.from_user.id, awards_delta=15)
                await user_microchalenges.increase_level(callback.from_user.id)
                await user_microchalenges.delete_challenge(callback.from_user.id)
        await user_microchalenges.update_personal_record(callback.from_user.id)
        await user_microchalenges.update_last_response(callback.from_user.id)
        await callback.message.answer("Это часть пути. Продолжай двигаться вперед.", reply_markup=keyboards.main(locale))
        
        
    else:
        await callback.message.answer(locale.error())
        
        
@router.callback_query(F.data == "btn3")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_microchalenges: UserMicroChallenge
            ):
    await state.clear()
    await callback.message.delete()
    res = await user_microchalenges.get_challenge(callback.from_user.id)
    if res != None:
        moscow_tz = pytz.timezone('Europe/Moscow')
        # Текущее время в Москве
        now = datetime.now(moscow_tz)

        # Создаем объект для сегодняшнего 19:00
        today_19 = now.replace(hour=19, minute=0, second=0, microsecond=0)

        # Если сейчас уже после 19:00, считаем до завтра в 19:00
        if now >= today_19:
            target_time = today_19 + timedelta(days=1)
        else:
            target_time = today_19
        level1 = await user_microchalenges.get_level(callback.from_user.id, 'porn')
        # Вычисляем разницу в секундах
        seconds_until = int((target_time - now).total_seconds())
        print(f"Секунд до ближайшего 19:00 по Москве: {seconds_until}")
        if level1 == 1:
            if int(res['personal_record']) <= 5:
                await db_nosql.schedule_message(callback.from_user.id, daily_messages[int(res['personal_record'])+1], 5, await keyboards.inline_check(), hide=True)
            else:
                stats = await user_cache.get_stats(callback.from_user.id)
                print(stats)
                if stats['status'] == 'user':
                    await db_nosql.schedule_message(callback.from_user.id, f"Поздравляю, челендж завершен!\n\n<i>К сожалению для повышения уровня челенджа требуется премиум</i>", 10, hide=True)

                else:
                    await db_nosql.schedule_message(callback.from_user.id, f"Поздравляю, челендж завершен!\n\n<i>Уровень челенджа можно повысить в каталоге, удачи, я верю в тебя</i>", 10, hide=True)

                await user_cache.update_stats(callback.from_user.id, awards_delta=15)
                await user_microchalenges.increase_level(callback.from_user.id)
                await user_microchalenges.delete_challenge(callback.from_user.id)
        else:
            if int(res['personal_record']) <= 11:
                await db_nosql.schedule_message(callback.from_user.id, daily_message_premium[int(res['personal_record'])+1], 5, await keyboards.inline_check(), hide=True)
            else:
                stats = await user_cache.get_stats(callback.from_user.id)
                print(stats)
                await db_nosql.schedule_message(callback.from_user.id, f"Поздравляю, челендж завершен!\n\n<i>К сожалению повышение уровня недоступно, мы ведем работу над новым курсом!</i>", 10, hide=True)


                await user_cache.update_stats(callback.from_user.id, awards_delta=15)
                await user_microchalenges.increase_level(callback.from_user.id)
                await user_microchalenges.delete_challenge(callback.from_user.id)
        await user_microchalenges.update_personal_record(callback.from_user.id)
        await user_microchalenges.update_last_response(callback.from_user.id)
        await callback.message.answer("Это не повод сдаваться, мы все совершаем ошибки, главное осознать ее причину", reply_markup=keyboards.main(locale))
        
        
    else:
        await callback.message.answer(locale.error())
        
        
@router.callback_query(F.data == "set_premium")
async def _(callback: CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            user_cache: UserCache,
            state: FSMContext,
            user_microchalenges: UserMicroChallenge
            ): 
    await callback.message.delete()
    await state.set_state(Adminpanel.set_premium)