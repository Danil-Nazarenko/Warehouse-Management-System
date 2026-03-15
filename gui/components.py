import customtkinter as ctk

# Обычное поле с хоткеями
class OrdoEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        events = ["<Control-v>", "<Control-V>", "<Control-a>", "<Control-A>", "<Control-c>", "<Control-C>"]
        for event in events:
            self.bind(event, self._handle_shortcuts)
            self._entry.bind(event, self._handle_shortcuts)

    def _handle_shortcuts(self, event):
        key = event.keysym.lower()
        if key == "v": return self._custom_paste()
        elif key == "a": return self._select_all()
        elif key == "c": return self._custom_copy()

    def _custom_paste(self, event=None):
        try:
            text = self.clipboard_get()
            if text:
                if self.selection_present():
                    self.delete("sel.first", "sel.last")
                self.insert("insert", text)
        except: pass
        return "break"

    def _custom_copy(self, event=None):
        if self.selection_present():
            try:
                text = self.get()[self.index("sel.first"):self.index("sel.last")]
                self.clipboard_clear()
                self.clipboard_append(text)
            except: pass
        return "break"

    def _select_all(self, event=None):
        self.select_range(0, "end")
        self.icursor("end")
        return "break"
    

class SmartSearchEntry(ctk.CTkEntry):
    def __init__(self, master, placeholder_text="Поиск...", width=300, **kwargs):
        # Работаем с переменной (либо переданной, либо создаем свою)
        self.internal_var = kwargs.get("textvariable") or ctk.StringVar()
        if "textvariable" in kwargs:
            del kwargs["textvariable"]

        super().__init__(
            master, 
            placeholder_text=placeholder_text, 
            width=width, 
            textvariable=self.internal_var, 
            **kwargs
        )
        
        self.on_search_callbacks = []
        self._after_id = None
        # Вешаем отслеживание ввода
        self.internal_var.trace_add("write", self._on_type)

    def _on_type(self, *args):
        """Метод вызывается при каждом изменении текста."""
        # Если таймер уже запущен — сбрасываем (дебаунсинг)
        if self._after_id:
            self.after_cancel(self._after_id)
        
        # Запускаем таймер на 400мс. Поиск сработает, только если ты перестанешь печатать.
        self._after_id = self.after(400, self._execute_search)

    def _execute_search(self):
        """Реальное выполнение поиска после паузы."""
        query = self.internal_var.get().strip().lower()
        
        # ЖЕСТКОЕ УСЛОВИЕ:
        # 1. Если поле пустое (сброс поиска) — вызываем обновление.
        # 2. Если введено 3 и более символов — вызываем обновление.
        # В остальных случаях (1-2 символа) программа просто молчит.
        if len(query) == 0 or len(query) >= 3:
            for callback in self.on_search_callbacks:
                callback()
        
        self._after_id = None

    def bind_search(self, callback):
        """Регистрирует внешнюю функцию (например, refresh из InventoryFrame)."""
        self.on_search_callbacks.append(callback)