import catalog_service
import warehouse_service
import supply_service
import waste_service
import data_manager  # Добавили для чтения остатков

def show_inventory():
    """Функция для красивого вывода остатков в консоль"""
    inventory = data_manager.load_json('inventory')
    
    print("\n" + "-"*60)
    print(f"{'АРТИКУЛ':<45} | {'ОСТАТОК':<10}")
    print("-"*60)
    
    if not inventory:
        print("На складе пока пусто.")
    else:
        # Сортируем по алфавиту для удобства
        for sku in sorted(inventory.keys()):
            qty = inventory[sku]
            # Визуальный индикатор: если товара меньше 5, ставим красный кружок
            status = "🔴" if qty < 5 else "🟢"
            print(f"{sku:<45} | {qty:<10} {status}")
    print("-"*60)

def main():
    while True:
        print("\n" + "="*30)
        print("   СИСТЕМА УПРАВЛЕНИЯ СКЛАДОМ")
        print("="*30)
        print("1. 📦 Каталог: Новый товар / Набор")
        print("2. 🚛 Поставка: Приход товара на склад")
        print("3. 📑 Утро: Загрузить заказы (Excel/CSV)")
        print("4. 🛠 Брак: Списать поврежденный товар")
        print("5. 📊 Склад: Просмотр текущих остатков") # Новый пункт
        print("6. 🚪 Выход")
        
        choice = input("\nВыберите действие: ")

        if choice == '1':
            catalog_service.create_new_product()
        elif choice == '2':
            supply_service.add_supply()
        elif choice == '3':
            fname = input("Имя файла заказа: ")
            warehouse_service.process_morning_orders(fname)
        elif choice == '4':
            waste_service.report_defect()
        elif choice == '5':
            show_inventory() # Вызов функции просмотра
        elif choice == '6':
            print("До свидания!")
            break
        else:
            print("Неверный пункт меню.")

if __name__ == "__main__":
    main()