import flet as ft

class CountingApp(ft.Page):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.text_field = ft.Text(value="Count: 0")
        self.append(
            ft.ElevatedButton(text="Increment", on_click=self.increment_count),
            self.text_field
        )

    def increment_count(self, e):
        self.count += 1
        self.text_field.value = f"Count: {self.count}"
        self.update()

def main(page: ft.Page):
    page.title = "Counting App"
    page.horizontal_alignment = "center"
    page.update()
    page.controls.append(CountingApp())

ft.app(target=main)
