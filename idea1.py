import flet as ft


def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "YF AI Private code writer"
    page.bgcolor = ft.Colors.BLACK

    title = ft.Text(
        "YF AI SECURE CODE WRITER",
        size=30,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.AMBER,
    )

    chat_history = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    user_input = ft.TextField(
        hint_text="Type your code...",
        expand=True,
        bgcolor=ft.Colors.BLACK,
        border_color=ft.Colors.AMBER,
        focused_border_color=ft.Colors.AMBER,
    )

    def send_click(e):
        if user_input.value:
            chat_history.controls.append(
                ft.Text(
                    f"You: {user_input.value}",
                    color=ft.Colors.WHITE,
                )
            )
            user_input.value = ""
            page.update()

    send_btn = ft.ElevatedButton(
        "Send",
        on_click=send_click,
    )

    input_row = ft.Row(
        controls=[
            user_input,
            send_btn,
        ]
    )

    # Everything inside this container
    app_content = ft.Column(
        controls=[
            ft.Row(
                controls=[title],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            chat_history,
            input_row,
        ],
        expand=True,
    )

    # GOLD BORDER AROUND THE WHOLE APP
    app_border = ft.Container(
        content=app_content,
        expand=True,
        bgcolor=ft.Colors.BLACK,
        border=ft.Border.all(
            width=3,
            color=ft.Colors.AMBER,
        ),
        padding=15,
    )

    page.add(app_border)


ft.app(main)