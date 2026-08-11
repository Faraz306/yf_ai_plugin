import flet as ft

def main(page: ft.Page):
    page.title = "ROI Finder"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # ROI Calculator
    def calculate_roi():
        initial_investment = float(page.controls[0].value)
        annual_return = float(page.controls[1].value)
        years = int(page.controls[2].value)
        roi = (annual_return / 100) * initial_investment * years
        page.controls[3].text = f"ROI: {roi:.2f}%"

    # UI Elements
    page.add(ft.Text("Initial Investment:", text_align=ft.TextAlign.LEFT),
             ft.TextField(hint_text="Enter initial investment", width=200),
             ft.Text("Annual Return (%):", text_align=ft.TextAlign.LEFT),
             ft.TextField(hint_text="Enter annual return", width=200),
             ft.Text("Years:", text_align=ft.TextAlign.LEFT),
             ft.TextField(hint_text="Enter years", width=200),
             ft.ElevatedButton("Calculate ROI", on_click=calculate_roi),
             ft.Text(""))

    page.update()

ft.app(target=main)
