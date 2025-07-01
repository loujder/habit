import logging
from typing import Any, Awaitable, Callable, Dict


from fluentogram import TranslatorHub
from aiogram import BaseMiddleware
from aiogram.types import Update
from shared.utils.db_nosql import UserCache





logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")



class TranslateMiddleware(BaseMiddleware):
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        language = data["user"].language_code if 'user' in data else 'ru'
        
        hub: TranslatorHub = data.get('t_hub')
        
        data['locale'] = hub.get_translator_by_locale(language)

        return await handler(event, data)
    
class CacheMiddleware(BaseMiddleware):
    def __init__(self, cache: UserCache):
        super().__init__()
        self.cache = cache

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        # Добавляем кеш в данные, которые будут переданы в обработчик
        data["user_cache"] = self.cache
        
        # Продолжаем обработку
        return await handler(event, data)
    
    
class CacheFriendsMiddleware(BaseMiddleware):
    def __init__(self, cache: UserCache):
        super().__init__()
        self.cache = cache

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        # Добавляем кеш в данные, которые будут переданы в обработчик
        data["user_friends"] = self.cache
        
        # Продолжаем обработку
        return await handler(event, data)


class CacheMicrochalengesMiddleware(BaseMiddleware):
    def __init__(self, cache: UserCache):
        super().__init__()
        self.cache = cache

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        # Добавляем кеш в данные, которые будут переданы в обработчик
        data["user_microchalenges"] = self.cache
        
        # Продолжаем обработку
        return await handler(event, data)

class CacheReferallsMiddleware(BaseMiddleware):
    def __init__(self, cache: UserCache):
        super().__init__()
        self.cache = cache

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        # Добавляем кеш в данные, которые будут переданы в обработчик
        data["user_referalls"] = self.cache
        
        # Продолжаем обработку
        return await handler(event, data)

    
