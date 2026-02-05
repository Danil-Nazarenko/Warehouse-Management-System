import data_manager

def add_supply():
    inventory = data_manager.load_json('inventory')
    recipes = data_manager.load_json('recipes')
    
    print("\n--- ПРИЕМКА ТОВАРА ---")
    sku = input("Введите артикул прибывшего товара: ").strip()
    
    # Проверяем, существует ли артикул в принципе
    if sku not in recipes:
        print(f"⚠️ Артикул '{sku}' не найден в каталоге!")
        create = input("Сначала завести этот товар в систему? (д/н): ")
        if create.lower() == 'д':
            import catalog_service
            catalog_service.create_new_product()
            inventory = data_manager.load_json('inventory') # Перезагружаем после создания
        else:
            return

    try:
        amount = int(input(f"Сколько единиц '{sku}' пришло?: "))
        if sku not in inventory:
            inventory[sku] = 0
        
        inventory[sku] += amount
        data_manager.save_json('inventory', inventory)
        print(f"✅ Успешно! Новый остаток '{sku}': {inventory[sku]}")
    except ValueError:
        print("❌ Ошибка: нужно ввести целое число.")