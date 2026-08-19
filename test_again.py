import flet
from flet import Page, TextField, ElevatedButton, Text, Row, Column, padding, alignment


def calculate_roi(initial_investment: float, final_value: float) -> float:
    """Calculate Return on Investment (ROI) as a percentage.

    Args:
        initial_investment: The amount initially invested.
        final_value: The final value of the investment.

    Returns:
        ROI percentage.
    """
    if initial_investment == 0:
        return 0.0
    return ((final_value - initial_investment) / initial_investment) * 100.0


def main(page: Page):
    page.title = "ROI Calculator"
    page.horizontal_alignment = alignment.center
    page.vertical_alignment = alignment.center

    # Input fields
    tf_initial = TextField(label="Initial Investment", hint_text="e.g., 1000", width=300, keyboard_type="number")
    tf_final = TextField(label="Final Value", hint_text="e.g., 1200", width=300, keyboard_type="number")
    txt_result = Text(value="", size=20, weight="bold")

    def on_calculate(e):
        try:
            initial = float(tf_initial.value)
            final = float(tf_final.value)
            roi = calculate_roi(initial, final)
            txt_result.value = f"ROI: {roi:.2f}%"
        except Exception as exc:
            txt_result.value = f"Error: {exc}"
        page.update()

    btn_calc = ElevatedButton(text="Calculate ROI", on_click=on_calculate)

    page.add(
        Column(
            controls=[
                tf_initial,
                tf_final,
                btn_calc,
                txt_result,
            ],
            alignment="center",
            horizontal_alignment="center",
            spacing=20,
            padding=padding.all(20),
        )
    )


# Run the app
if __name__ == "__main__":
    flet.app(target=main, view=flet.FLET_APP)
