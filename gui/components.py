import customtkinter as ctk

class OrdoEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # Привязываем событие ко всему окну, но только когда фокус на этом поле
        # Это самый мощный способ заставить хоткеи работать
        self._entry.bind("<KeyPress>", self._check_hotkeys)

    def _check_hotkeys(self, event):
        # Проверяем, нажат ли Control (маска 4)
        ctrl_pressed = (event.state & 0x4) != 0
        
        # Физические коды клавиш (не зависят от языка): 86=V, 67=C, 65=A
        if ctrl_pressed:
            if event.keycode == 86 or event.keysym.lower() in ('v', 'м'):
                self._force_paste()
                return "break"
            elif event.keycode == 67 or event.keysym.lower() in ('c', 'с'):
                self._force_copy()
                return "break"
            elif event.keycode == 65 or event.keysym.lower() in ('a', 'ф'):
                self._force_select_all()
                return "break"

    def _force_paste(self):
        try:
            # Берем текст из буфера обмена через встроенный метод tkinter
            text = self.focus_get().clipboard_get()
            if text:
                # Если текст выделен — заменяем его
                if self._entry.selection_present():
                    self._entry.delete("sel.first", "sel.last")
                self._entry.insert("insert", text)
        except:
            pass

    def _force_copy(self):
        try:
            if self._entry.selection_present():
                selected_text = self._entry.get()[self._entry.index("sel.first"):self._entry.index("sel.last")]
                self.clipboard_clear()
                self.clipboard_append(selected_text)
        except:
            pass

    def _force_select_all(self):
        self._entry.tag_add("sel", "0", "end")
        self._entry.mark_set("insert", "end")
        self._entry.focus_set()

class SmartSearchEntry(OrdoEntry):
    def __init__(self, master, placeholder_text="Поиск...", width=300, **kwargs):
        # Извлекаем переменную поиска, если она передана
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
        self.internal_var.trace_add("write", self._on_type)

    def _on_type(self, *args):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(400, self._execute_search)

    def _execute_search(self):
        query = self.internal_var.get().strip().lower()
        if len(query) == 0 or len(query) >= 3:
            for callback in self.on_search_callbacks:
                callback()
        self._after_id = None

    def bind_search(self, callback):
        self.on_search_callbacks.append(callback)