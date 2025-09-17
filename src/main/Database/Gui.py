import tkinter as tk


class PizzaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pizza Crisis App")
        self.geometry("325x400")
        self.configure(bg="white")

        # container for all screens
        self.container = tk.Frame(self, width=325, height=400, bg="white")
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (HomeScreen, MenuScreen, OrderScreen, ReportsScreen):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(HomeScreen)

    def show_frame(self, page):
        frame = self.frames[page]
        frame.tkraise()




def place_order_action():
    # for now just print
    print("Order placed successfully!")
    # Reminder for me for later: save to DB, assign delivery, apply discounts... etc. instead of just printing.


class HomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        center_frame = tk.Frame(self, bg="white")
        center_frame.pack(expand=True)

        label = tk.Label(center_frame, text="Welcome to Pizza Crisis App!",
                         font=("Arial", 18), fg="red", bg="white")
        label.pack(pady=20)

        btn_menu = tk.Button(center_frame, text="View Menu", font=("Arial", 14),
                             command=lambda: controller.show_frame(MenuScreen))
        btn_menu.pack(pady=10)

        btn_order = tk.Button(center_frame, text="Place Order", font=("Arial", 14),
                              command=place_order_action)
        btn_order.pack(pady=10)

        btn_reports = tk.Button(center_frame, text="Staff Reports", font=("Arial", 14),
                                command=lambda: controller.show_frame(ReportsScreen))
        btn_reports.pack(pady=10)

class MenuScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        label = tk.Label(self, text="Menu Screen", font=("Arial", 16), bg="white")
        label.pack(pady=20)

        back = tk.Button(self, text="Back", command=lambda: controller.show_frame(HomeScreen))
        back.pack()


class OrderScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        label = tk.Label(self, text="Order Screen", font=("Arial", 16), bg="white")
        label.pack(pady=20)

        back = tk.Button(self, text="Back", command=lambda: controller.show_frame(HomeScreen))
        back.pack()


class ReportsScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        label = tk.Label(self, text="Reports Screen", font=("Arial", 16), bg="white")
        label.pack(pady=20)

        back = tk.Button(self, text="Back", command=lambda: controller.show_frame(HomeScreen))
        back.pack()

# Run App
if __name__ == "__main__":
    app = PizzaApp()
    app.mainloop()
