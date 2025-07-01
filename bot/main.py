from fluentogram import TranslatorHub, FluentTranslator
from fluent_compiler.bundle import FluentBundle
import logging
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
import asyncio
from shared.utils.db_sql import init_db


from shared.utils.config import settings
from shared.utils.middlewares import TranslateMiddleware, CacheMiddleware, CacheFriendsMiddleware, CacheMicrochalengesMiddleware, CacheReferallsMiddleware
from src.handlers import router as main_router
from motor.motor_asyncio import AsyncIOMotorClient
from shared.utils.db_nosql import UserCache, UserFriends, UserMicroChallenge, Referrals

# Инициализация MongoDB клиента (как у вас уже есть)
mongo_client = AsyncIOMotorClient(
    f'mongodb://{settings.MONGO_USERNAME}:'
    f'{settings.MONGO_PASSWORD}@'
    f'{settings.MONGO_HOST}:'
    f'{settings.MONGO_PORT}'
)

external_client = AsyncIOMotorClient(
    f'mongodb://{settings.MONGO_USERNAME}:'
    f'{settings.MONGO_PASSWORD}@'
    f'{settings.MONGO_HOST_EXTERNAL}:'
    f'{settings.MONGO_PORT_EXTERNAL}'
)


# Инициализация кеша
user_cache = UserCache(
    mongo_client=mongo_client,
    mongo_db_name=settings.MONGO_DB_NAME,
    mongo_collection=settings.MONGO_COLLECTION
)
user_friends = UserFriends(
    mongo_client=mongo_client
)

user_microchalenges = UserMicroChallenge(mongo_client=mongo_client)

user_referals = Referrals(mongo_client=mongo_client)



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

t_hub = TranslatorHub(
    {
        "ru": ("ru", )
    },
    translators=[
        FluentTranslator(
            'ru',
            translator=FluentBundle.from_files(
                "ru-RU",
                filenames=[
                    'shared/i18n/ru/text.ftl',
                    'shared/i18n/ru/button.ftl'
                ]
            ),
        )
    ],
    root_locale='ru'
)

async def main():
    await init_db()
    await user_cache.initialize()
    await user_friends.initialize()
    await user_microchalenges.initialize()
    await user_referals.initialize()
    session = AiohttpSession()
    bot = Bot(
        token = settings.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    storage=RedisStorage.from_url(
        url=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
    )
    dp = Dispatcher(storage=storage, t_hub=t_hub)
    dp.message.outer_middleware(TranslateMiddleware())
    dp.message.outer_middleware(CacheMiddleware(user_cache))
    dp.message.outer_middleware(CacheFriendsMiddleware(user_friends))
    dp.message.outer_middleware(CacheMicrochalengesMiddleware(user_microchalenges))
    dp.message.outer_middleware(CacheReferallsMiddleware(user_referals))
    dp.callback_query.outer_middleware(TranslateMiddleware())
    dp.callback_query.outer_middleware(CacheMiddleware(user_cache))
    dp.callback_query.outer_middleware(CacheFriendsMiddleware(user_friends))
    dp.callback_query.outer_middleware(CacheMicrochalengesMiddleware(user_microchalenges))
    dp.callback_query.outer_middleware(CacheReferallsMiddleware(user_referals))
    
    
    dp.include_router(main_router)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Error {e}")
    finally:
        
        await bot.session.close()
        
        
if __name__ == "__main__":
    asyncio.run(main())