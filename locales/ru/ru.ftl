mood-unset = Не указано
mood-awesome = Прекрасно
mood-greet = Здорово
mood-good = Хорошо
mood-okay = Обычно
mood-bad = Плохо
mood-terrible = Ужасно

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

error-button_wrong_user = Не твоя кнопка

mood_month = 
    <tg-emoji emoji-id="5431897022456145283">📆</tg-emoji> Календарь настроения
    
    <b>{ $year }, { $month }</b>

mood_day =
    <tg-emoji emoji-id="5471978009449731768">👉</tg-emoji> <b>{ $year }, { $month }, { $day }</b>

    { $mood ->
        [unset] 
        Как прошёл этот день?
        *[other]
        День прошел — { $mood_emoji } { $mood -> 
            [awesome] { mood-awesome }
            [greet] { mood-greet }
            [good] { mood-good }
            [okay] { mood-okay }
            [bad] { mood-bad }
            [terrible] { mood-terrible }
            *[other] {""}
        }
    }

mood_marker_selected = ✏️ Выбрано: { $marker }
clear = Очистить