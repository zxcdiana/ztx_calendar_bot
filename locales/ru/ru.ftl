bot_command-mood = Календарь настроения
bot_command-notify = Уведомления
bot_command-tz = Установить время
bot_command-start = /start

error-button_wrong_user = Не твоя кнопка

mood-unset = Не указано
mood-awesome = Прекрасно
mood-greet = Здорово
mood-good = Хорошо
mood-okay = Обычно
mood-bad = Плохо
mood-terrible = Ужасно

mood_month = 
    <tg-emoji emoji-id="5431897022456145283">📆</tg-emoji> Календарь настроения
    
    <b>{ $year }, { $month }</b>

    <i>Текущая дата: { $current_dmy }</i>


mood_day-main_panel =
    <tg-emoji emoji-id="5471978009449731768">👉</tg-emoji> <b>{ $year }, { $month }, { $day }</b>

    { $mood ->
        [unset] 
        Как прошёл этот день?
        *[other]
        День прошёл — { $mood_emoji } { $mood -> 
            [awesome] { mood-awesome }
            [greet] { mood-greet }
            [good] { mood-good }
            [okay] { mood-okay }
            [bad] { mood-bad }
            [terrible] { mood-terrible }
            *[other] {""}
        }
    }

    { $note ->
        [none] {""}
        *[other] <blockquote expandable>{ $note }</blockquote> 
    }

mood_day-add_note = ✏️ Добавить заметку 
mood_day-edit_note =  Ред. ✏️
mood_day-extend_note =  Доп. ✏️
mood_day-delete_note = 🗑 Удалить заметку

mood_day-note_too_long =
    🚫 <b>Превышен лимит объёма заметки</b>

    Колличество символов: { $lenght }
    Необходимо сократить заметку до { $limit } символов

mood_day-edit_note_panel =
    <tg-emoji emoji-id="5431897022456145283">📆</tg-emoji> <b>{ $dmy }, { $weekday }</b>

    { $action ->
        [edit]
        ✏️ <b>Редактирование заметки</b>

        Отправь заметку для этого дня:
        [extend]
        ✏️ <b>Дополнение заметки</b>
        
        Отправь дополнение к текущей заметке:
        *[other] {""}
    }


mood_day-delete_note_warning =
    <tg-emoji emoji-id="5431897022456145283">📆</tg-emoji> <b>{ $dmy }, { $weekday }</b>

    ⚠️ <b>Удалить заметку?</b>

mood_day-note_deleted = Заметка удалена
mood_day-note_saved = Заметка сохранена


mood_marker_selected = ✏️ Выбрано: { $marker }


clear = Очистить
cancel = Отменить
close = Закрыть
back = Назад


command-start =
    привет, { $user_name }


mood_notify-disabled =
    Хочешь получать ежедневные напоминания о заполнении календаря?

mood_notify-enabled =
    <tg-emoji emoji-id="5449505950283078474">❤️</tg-emoji> Я буду отправлять тебе напоминания { $chat ->
                                                                                            [pm] в ЛС
                                                                                            *[other] в чат { $chat }
                                                                                                },
    чтобы ты заполнил { $day ->
                        [current] текущий день.
                        [previos] предыдущий день.
                        *[other] день.
                    }

    Каждый день в { $time }

mood_notify-notify_current_day = Напоминать текущий
mood_notify-notify_previos_day = Напоминать предыдущий

turn_on = Включить
turn_off = Выключить
change = сменить
send_here = Отправлять в этот чат
send_pm = Отправлять в ЛС
loading = Загрузка...


mood_notify-select_time =
    Укажи время, в которое тебе будет удобно получать напоминания

mood_notify-notification =
    Привет, { $user_name }
    { $day ->
        [previos]
        Как прошёл вчерашний день?
        *[current]
        Как прошёл день?
    }

    <tg-emoji emoji-id="5431897022456145283">📆</tg-emoji> <b>{ $dmy }, { $weekday }</b>


gender-male = 🙍‍♂️ Мужской
gender-female = 🙇‍♀️ Женский

gender-male_button = Пол: { gender-male }
gender-female_button = Пол: { gender-female }
gender-changed = Пол сохранен

tz_command-info =
    <b>Время у тебя:</b>
    { $time_emoji } <code>{ $date_time }</code>

    Для смены времени введи:
    &gt; <code>{ $command } город</code>

tz_command-changed =
     Время установлено!
    { $time_emoji } <code>{ $date_time }</code>

tz_command-timezone404 =
    <tg-emoji emoji-id='5465665476971471368'>❌</tg-emoji> Не удалось найти локацию по запросу «<code>{ $query }</code>»

month_1 = Январь
month_2 = Февраль
month_3 = Март
month_4 = Апрель
month_5 = Май
month_6 = Июнь
month_7 = Июль
month_8 = Август
month_9 = Сентябрь
month_10 = Октябрь
month_11 = Ноябрь
month_12 = Декабрь


weekday_1 = Понедельник
weekday_2 = Вторник
weekday_3 = Среда
weekday_4 = Четверг
weekday_5 = Пятница
weekday_6 = Суббота
weekday_7 = Воскресенье