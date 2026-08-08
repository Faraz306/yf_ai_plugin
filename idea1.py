import flet as ft

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "YF Security Guard"
    page.add(
        ft.Row(
            controls=[
                ft.Text(
                    value="YF SECURITY GUARD",
                    size=30,
                    weight=ft.FontWeight.BOLD, color="golden"
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
    )

    # 1. This list expands to fill all space, pushing the input down
    chat_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    # 2. Your input field
    user_input = ft.TextField(hint_text="Type your code...", expand=True)

    def send_click(e):
        if user_input.value:
            # Append message to list - it stays on screen
            chat_history.controls.append(ft.Text(f"You: {user_input.value}"))
            user_input.value = ""  # Clear input
            page.update()         # Update screen to show new message

    # 3. Create the Row for the bottom of the screen
    send_btn = ft.ElevatedButton("Send", on_click=send_click)
    input_row = ft.Row(controls=[send_btn])

    # 4. Add them in this order: history on top, row on bottom
    page.add(chat_history, input_row, user_input)

ft.app(main) # Use the modern run command

