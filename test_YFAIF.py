import flet
from flet import Page, TextField, ElevatedButton, Text, Row, Column, padding, alignment

def main(page: Page):
    page.title = "Return on Investment (ROI) Calculator"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"

    # Input fields
    investment_input = TextField(label="Initial Investment ($)", width=300, keyboard_type="number")
    rate_input = TextField(label="Annual Return Rate (%)", width=300, keyboard_type="number")
    years_input = TextField(label="Number of Years", width=300, keyboard_type="number")

    result_text = Text("", size=20, weight="bold")

    def calculate(e):
        try:
            principal = float(investment_input.value or 0)
            rate_percent = float(rate_input.value or 0)
            years = int(years_input.value or 0)
            rate = rate_percent / 100.0
            # Future value formula
            future_value = principal * ((1 + rate) ** years)
            roi = future_value - principal
            result_text.value = f"Future Value: ${future_value:,.2f}   ROI: ${roi:,.2f}"
        except ValueError:
            result_text.value = "Please enter valid numeric values."
        page.update()

    calculate_button = ElevatedButton(text="Calculate ROI", on_click=calculate)

    page.add(
        Column(
            controls=[
                Text("Return on Investment Calculator", size=24, weight="bold"),
                investment_input,
                rate_input,
                years_input,
                calculate_button,
                result_text,
            ],
            alignment="center",
            horizontal_alignment="center",
            spacing=10,
        )
    )

flet.app(target=main, view=flet.FLET_APP)
