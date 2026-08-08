import flet as ft


def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "YF Security Guard"

    title = ft.Text(
        value="YF SECURITY GUARD",
        size=30,
        weight=ft.FontWeight.BOLD,
        color="golden",
    )

    chat_history = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    user_input = ft.TextField(
        hint_text="Type your code...",
        expand=True,
    )

    def send_click(e):
        if user_input.value:
            chat_history.controls.append(
                ft.Text(f"You: {user_input.value}")
            )

            user_input.value = ""
            page.update()

    send_btn = ft.ElevatedButton(
        "Send",
        on_click=send_click,
    )

    # Input + button permanently at the bottom
    input_row = ft.Row(
        controls=[
            user_input,
            send_btn,
        ]
    )

    page.add(
        ft.Row(
            controls=[title],
            alignment=ft.MainAxisAlignment.CENTER,
        ),

        # Chat takes all remaining space
        chat_history,

        # Bottom input
        input_row,
    )


ft.app(main)