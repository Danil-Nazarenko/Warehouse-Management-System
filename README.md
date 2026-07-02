# Warehouse Management System

Небольшое desktop-приложение для учёта склада, которое я написал на Python + CustomTkinter. Изначально делал под конкретную задачу — вести остатки, приход и списания без Excel-таблиц, которые постоянно расходились между собой.

## Что умеет

- Смотреть текущие остатки по складу
- Вести раздел "Актуальное" — то, что нужно держать в фокусе прямо сейчас
- Оформлять загрузку/отгрузку
- Принимать приход товара
- Делать замену одной позиции на другую (без ручного пересчёта остатков)
- Списывать брак/недостачу
- Вести каталог позиций
- Смотреть историю всех операций
- Проверять обновления приложения прямо из интерфейса

## На чём написано

- Python
- CustomTkinter для интерфейса
- SQLite как база данных (`database.py`)

## Структура

```
main.py                # запуск приложения, навигация по разделам
database.py            # подключение к БД и её инициализация
data_manager.py        # общая работа с данными
catalog_service.py     # каталог товаров
supply_service.py      # приход
warehouse_service.py   # остатки на складе
waste_service.py       # списания
active_view.py         # "актуальное"
gui/                   # экраны интерфейса
    inventory_frame.py
    inventory_operations.py
    shipping_frame.py
    catalog_frame.py
    history_view.py
    updater_service.py
version.txt            # версия приложения
```

## Как запустить

```bash
git clone https://github.com/Danil-Nazarenko/Warehouse-Management-System.git
cd Warehouse-Management-System
pip install customtkinter
python main.py
```

Python 3.10+, желательно ставить в виртуальное окружение, но не обязательно.

## Статус

Пока пилю в свободное время, добавляю функционал по мере необходимости. Баги и предложения — welcome.
