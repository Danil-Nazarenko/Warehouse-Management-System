import data_manager

def report_defect():
    inventory = data_manager.load_json('inventory')
    
    print("\n--- СПИСАНИЕ БРАКА ---")
    sku = input("Введите артикул бракованного товара: ").strip()
    
    if sku not in inventory:
        print(f"❌ Товара '{sku}' нет на остатках.")
        return

    try:
        amount = int(input(f"Сколько единиц '{sku}' списать как брак?: "))
        if amount > inventory[sku]:
            print(f"⚠️ Внимание: на складе всего {inventory[sku]}, а вы списываете {amount}.")
            confirm = input("Продолжить? (д/н): ")
            if confirm.lower() != 'д': return

        inventory[sku] -= amount
        data_manager.save_json('inventory', inventory)
        print(f"✅ Списано. Остаток '{sku}': {inventory[sku]}")
        
        # Здесь в будущем можно добавить запись в файл log.txt для истории
    except ValueError:
        print("❌ Ошибка: нужно ввести целое число.")