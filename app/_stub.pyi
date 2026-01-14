# mypy: ignore-errors
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Literal, overload
from aiogram_i18n import LazyProxy

class I18nContext(I18nStub):

    def get(self, key: str, /, **kwargs: Any) -> str:
        ...

    async def set_locale(self, locale: str, **kwargs: Any) -> None:
        ...

    @contextmanager
    def use_locale(self, locale: str) -> Generator[I18nContext, None, None]:
        ...

    @contextmanager
    def use_context(self, **kwargs: Any) -> Generator[I18nContext, None, None]:
        ...

    def set_context(self, **kwargs: Any) -> None:
        ...

class LazyFactory(I18nStub):
    key_separator: str

    def set_separator(self, key_separator: str) -> None:
        ...

    def __call__(self, key: str, /, **kwargs: dict[str, Any]) -> LazyProxy:
        ...
L: LazyFactory

class I18nStub:

    class __BotCommand:

        @staticmethod
        def mood(**kwargs: Any) -> Literal['Календарь настроения']:
            ...

        @staticmethod
        def notify(**kwargs: Any) -> Literal['Уведомления']:
            ...

        @staticmethod
        def tz(**kwargs: Any) -> Literal['Установить время']:
            ...

        @staticmethod
        def start(**kwargs: Any) -> Literal['/start']:
            ...
    bot_command = __BotCommand()

    class __Error:

        @staticmethod
        def button_wrong_user(**kwargs: Any) -> Literal['Не твоя кнопка']:
            ...
    error = __Error()

    class __Mood:

        @staticmethod
        def unset(**kwargs: Any) -> Literal['Не указано']:
            ...

        @staticmethod
        def awesome(**kwargs: Any) -> Literal['Прекрасно']:
            ...

        @staticmethod
        def greet(**kwargs: Any) -> Literal['Здорово']:
            ...

        @staticmethod
        def good(**kwargs: Any) -> Literal['Хорошо']:
            ...

        @staticmethod
        def okay(**kwargs: Any) -> Literal['Обычно']:
            ...

        @staticmethod
        def bad(**kwargs: Any) -> Literal['Плохо']:
            ...

        @staticmethod
        def terrible(**kwargs: Any) -> Literal['Ужасно']:
            ...
    mood = __Mood()

    @staticmethod
    def mood_month(*, year: Any, month: Any, current_dmy: Any, **kwargs: Any) -> Literal['<tg-emoji emoji-id="5431897022456145283">📆</tg-emoji> Календарь настроения']:
        ...

    class __MoodDay:

        @staticmethod
        def main_panel(*, year: Any, month: Any, day: Any, mood: Any, mood_emoji: Any, note: Any, **kwargs: Any) -> Literal['<tg-emoji emoji-id="5471978009449731768">👉</tg-emoji> <b>{ $year }, { $month }, { $day }</b>']:
            ...

        @staticmethod
        def add_note(**kwargs: Any) -> Literal['✏️ Добавить заметку']:
            ...

        @staticmethod
        def edit_note(**kwargs: Any) -> Literal['Ред. ✏️']:
            ...

        @staticmethod
        def extend_note(**kwargs: Any) -> Literal['Доп. ✏️']:
            ...

        @staticmethod
        def delete_note(**kwargs: Any) -> Literal['🗑 Удалить заметку']:
            ...

        @staticmethod
        def note_too_long(*, lenght: Any, limit: Any, **kwargs: Any) -> Literal['🚫 <b>Превышен лимит объёма заметки</b>']:
            ...

        @staticmethod
        def edit_note_panel(*, dmy: Any, weekday: Any, action: Any, **kwargs: Any) -> Literal['<tg-emoji emoji-id="5431897022456145283">📆</tg-emoji> <b>{ $dmy }, { $weekday }</b>']:
            ...

        @staticmethod
        def delete_note_warning(*, dmy: Any, weekday: Any, **kwargs: Any) -> Literal['<tg-emoji emoji-id="5431897022456145283">📆</tg-emoji> <b>{ $dmy }, { $weekday }</b>']:
            ...

        @staticmethod
        def note_deleted(**kwargs: Any) -> Literal['Заметка удалена']:
            ...

        @staticmethod
        def note_saved(**kwargs: Any) -> Literal['Заметка сохранена']:
            ...
    mood_day = __MoodDay()

    @staticmethod
    def mood_marker_selected(*, marker: Any, **kwargs: Any) -> Literal['✏️ Выбрано: { $marker }']:
        ...

    @staticmethod
    def clear(**kwargs: Any) -> Literal['Очистить']:
        ...

    @staticmethod
    def cancel(**kwargs: Any) -> Literal['Отменить']:
        ...

    @staticmethod
    def close(**kwargs: Any) -> Literal['Закрыть']:
        ...

    @staticmethod
    def back(**kwargs: Any) -> Literal['Назад']:
        ...

    class __Command:

        @staticmethod
        def start(*, user_name: Any, **kwargs: Any) -> Literal['привет, { $user_name }']:
            ...
    command = __Command()

    class __MoodNotify:

        @staticmethod
        def disabled(**kwargs: Any) -> Literal['Хочешь получать ежедневные напоминания о заполнении календаря?']:
            ...

        @staticmethod
        def enabled(*, chat: Any, day: Any, time: Any, **kwargs: Any) -> Literal['<tg-emoji emoji-id="5449505950283078474">❤️</tg-emoji> Я буду отправлять тебе напоминания { $chat ->']:
            ...

        @staticmethod
        def notify_current_day(**kwargs: Any) -> Literal['Напоминать текущий']:
            ...

        @staticmethod
        def notify_previos_day(**kwargs: Any) -> Literal['Напоминать предыдущий']:
            ...

        @staticmethod
        def select_time(**kwargs: Any) -> Literal['Укажи время, в которое тебе будет удобно получать напоминания']:
            ...

        @staticmethod
        def notification(*, user_name: Any, day: Any, dmy: Any, weekday: Any, **kwargs: Any) -> Literal['Привет, { $user_name }']:
            ...
    mood_notify = __MoodNotify()

    @staticmethod
    def turn_on(**kwargs: Any) -> Literal['Включить']:
        ...

    @staticmethod
    def turn_off(**kwargs: Any) -> Literal['Выключить']:
        ...

    @staticmethod
    def change(**kwargs: Any) -> Literal['сменить']:
        ...

    @staticmethod
    def send_here(**kwargs: Any) -> Literal['Отправлять в этот чат']:
        ...

    @staticmethod
    def send_pm(**kwargs: Any) -> Literal['Отправлять в ЛС']:
        ...

    @staticmethod
    def loading(**kwargs: Any) -> Literal['Загрузка...']:
        ...

    class __Gender:

        @staticmethod
        def male(**kwargs: Any) -> Literal['🙍\u200d♂️ Мужской']:
            ...

        @staticmethod
        def female(**kwargs: Any) -> Literal['🙇\u200d♀️ Женский']:
            ...

        @staticmethod
        def male_button(**kwargs: Any) -> Literal['Пол: { gender-male }']:
            ...

        @staticmethod
        def female_button(**kwargs: Any) -> Literal['Пол: { gender-female }']:
            ...

        @staticmethod
        def changed(**kwargs: Any) -> Literal['Пол сохранен']:
            ...
    gender = __Gender()

    class __TzCommand:

        @staticmethod
        def info(*, time_emoji: Any, date_time: Any, command: Any, **kwargs: Any) -> Literal['<b>Время у тебя:</b>']:
            ...

        @staticmethod
        def changed(*, time_emoji: Any, date_time: Any, **kwargs: Any) -> Literal['Время установлено!']:
            ...

        @staticmethod
        def timezone404(*, query: Any, **kwargs: Any) -> Literal["<tg-emoji emoji-id='5465665476971471368'>❌</tg-emoji> Не удалось найти локацию по запросу «<code>{ $query }</code>»"]:
            ...
    tz_command = __TzCommand()

    @staticmethod
    def month_1(**kwargs: Any) -> Literal['Январь']:
        ...

    @staticmethod
    def month_2(**kwargs: Any) -> Literal['Февраль']:
        ...

    @staticmethod
    def month_3(**kwargs: Any) -> Literal['Март']:
        ...

    @staticmethod
    def month_4(**kwargs: Any) -> Literal['Апрель']:
        ...

    @staticmethod
    def month_5(**kwargs: Any) -> Literal['Май']:
        ...

    @staticmethod
    def month_6(**kwargs: Any) -> Literal['Июнь']:
        ...

    @staticmethod
    def month_7(**kwargs: Any) -> Literal['Июль']:
        ...

    @staticmethod
    def month_8(**kwargs: Any) -> Literal['Август']:
        ...

    @staticmethod
    def month_9(**kwargs: Any) -> Literal['Сентябрь']:
        ...

    @staticmethod
    def month_10(**kwargs: Any) -> Literal['Октябрь']:
        ...

    @staticmethod
    def month_11(**kwargs: Any) -> Literal['Ноябрь']:
        ...

    @staticmethod
    def month_12(**kwargs: Any) -> Literal['Декабрь']:
        ...

    @staticmethod
    def weekday_1(**kwargs: Any) -> Literal['Понедельник']:
        ...

    @staticmethod
    def weekday_2(**kwargs: Any) -> Literal['Вторник']:
        ...

    @staticmethod
    def weekday_3(**kwargs: Any) -> Literal['Среда']:
        ...

    @staticmethod
    def weekday_4(**kwargs: Any) -> Literal['Четверг']:
        ...

    @staticmethod
    def weekday_5(**kwargs: Any) -> Literal['Пятница']:
        ...

    @staticmethod
    def weekday_6(**kwargs: Any) -> Literal['Суббота']:
        ...

    @staticmethod
    def weekday_7(**kwargs: Any) -> Literal['Воскресенье']:
        ...