import data_manager

def create_new_product():
    """Интерфейс создания товара или комплекта."""
    recipes = data_manager.load_json('recipes')
    inventory = data_manager.load_json('inventory')

    print("\n--- МАСТЕР СОЗДАНИЯ ТОВАРА ---")
    sku_name = input("Введите Артикул Продавца (как в Excel): ").strip()
    
    if sku_name in recipes:
        print("⚠️ Этот товар уже есть в базе! Перезапись.")

    is_bundle = input("Это набор (комплект)? (д/н): ").lower()

    if is_bundle != 'д':
        # --- Логика для ПРОСТОГО товара ---
        try:
            qty = int(input(f"Текущий остаток '{sku_name}' на складе: "))
            inventory[sku_name] = qty
            recipes[sku_name] = "SIMPLE" # Маркер простого товара
            print(f"✅ Товар создан.")
        except ValueError:
            print("Ошибка: введите число!")
    
    else:
        # --- Логика для НАБОРА ---
        print(f"\nСобираем состав для '{sku_name}'. Enter для завершения.")
        components = {}
        
        while True:
            comp_sku = input("Артикул компонента: ").strip()
            if not comp_sku:
                break
            
            # Если компонента нет на складе, предлагаем создать
            if comp_sku not in inventory:
                print(f"⚠️ Компонент '{comp_sku}' не найден на складе.")
                create = input("Добавить его как простой товар? (д/н): ")
                if create.lower() == 'д':
                    qty_comp = int(input(f"Остаток '{comp_sku}': "))
                    inventory[comp_sku] = qty_comp
                    recipes[comp_sku] = "SIMPLE"
                else:
                    print("Компонент пропущен.")
                    continue

            try:
                comp_qty = int(input(f"Кол-во '{comp_sku}' в наборе: "))
                components[comp_sku] = comp_qty
            except ValueError:
                print("Нужно ввести число.")
        
        if components:
            recipes[sku_name] = components
            print(f"✅ Набор сохранен ({len(components)} компонентов).")
        else:
            print("❌ Набор пуст, не сохранен.")

    # Сохраняем изменения
    data_manager.save_json('recipes', recipes)
    data_manager.save_json('inventory', inventory)