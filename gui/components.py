import customtkinter as ctk

class OrdoEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Список событий для регистрации
        events = ["<Control-v>", "<Control-V>", "<Control-a>", "<Control-A>", "<Control-c>", "<Control-C>"]
        
        for event in events:
            # Биндим само поле
            self.bind(event, self._handle_shortcuts)
            # Биндим ВНУТРЕННЕЕ поле (самый важный момент для CTk)
            self._entry.bind(event, self._handle_shortcuts)

    def _handle_shortcuts(self, event):
        key = event.keysym.lower()
        
        if key == "v":
            return self._custom_paste()
        elif key == "a":
            return self._select_all()
        elif key == "c":
            return self._custom_copy()

    def _custom_paste(self, event=None):
        try:
            text = self.clipboard_get()
            if text:
                if self.selection_present():
                    self.delete("sel.first", "sel.last")
                # Вставляем в позицию курсора (insert)
                self.insert("insert", text)
        except:
            pass
        return "break"

    def _custom_copy(self, event=None):
        if self.selection_present():
            try:
                text = self.get()[self.index("sel.first"):self.index("sel.last")]
                self.clipboard_clear()
                self.clipboard_append(text)
            except:
                pass
        return "break"

    def _select_all(self, event=None):
        self.select_range(0, "end")
        self.icursor("end")
        return "break"