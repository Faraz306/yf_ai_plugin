import flet as ft


def calculate_roi(investment: float, returns: float) -> float:
    """Calculate Return on Investment (ROI) as a percentage.

    ROI = ((returns - investment) / investment) * 100
    """
    if investment == 0:
        return 0.0
    return ((returns - investment) / investment) * 100


def main(page: ft.Page):
    page.title = "ROI Calculator"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    investment_input = ft.TextField(label="Investment", hint_text="Enter investment amount", keyboard_type=ft.KeyboardType.NUMBER)
    returns_input = ft.TextField(label="Returns", hint_text="Enter returns amount", keyboard_type=ft.KeyboardType.NUMBER)
    result_text = ft.Text(value="ROI: ", size=20)

    def on_calculate(e):
        try:
            investment = float(investment_input.value)
            returns = float(returns_input.value)
            roi = calculate_roi(investment, returns)
            result_text.value = f"ROI: {roi:.2f}%"
        except ValueError:
            result_text.value = "Please enter valid numbers."
        page.update()

    calculate_button = ft.ElevatedButton(text="Calculate ROI", on_click=on_calculate)

    page.add(
        ft.Column([
            investment_input,
            returns_input,
            calculate_button,
            result_text,
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
    )


if __name__ == "__main__":
    ft.app(target=main)