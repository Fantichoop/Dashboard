@startuml

class Сайт

Человек -> Сайт: Заходит на сайт

Сайт -> Человек: Показывает результат

Сайт <- Таблица: Вывод данных

Сервер -> Таблица: Обработка данных

Сервер <-- Район: Загрузка данных

@enduml