import flet as ft

     def main(page: ft.Page):
         page.title = "ROI Automation Calculator"
         page.theme_mode = ft.ThemeMode.DARK

         manual_time_input = ft.NumberInput(label="Hours per manual task")
         frequency_input = ft.NumberInput(label="Tasks per month")
         coding_hours_input = ft.NumberInput(label="Hours to write code")

         result_text = ft.Text(value="", size=20)

         def calculate(e):
             manual = manual_time_input.value or 0
             freq = frequency_input.value or 0
             coding = coding_hours_input.value or 0

             annual_manual = manual * freq * 12
             maintenance = coding * 0.2 # 20% annual maintenance estimate
             total_cost = coding + maintenance
             hours_saved = annual_manual - total_cost

             # Assume $30/hr for cost calculation
             hourly_rate = 30
             cost_saved = hours_saved * hourly_rate
             maintenance_cost = maintenance * hourly_rate

             message = f"Annual Manual Hours: {annual_manual:.1f}\n"
             message += f"Development + Maintenance Hours: {total_cost:.1f}\n"
             message += f"Net Hours Saved: {hours_saved:.1f}\n"
             message += f"Estimated Cost Saved: ${cost_saved:.2f}\n"
             message += f"Annual Maintenance Cost: ${maintenance_cost:.2f}\n\n"

             if hours_saved > manual * freq * 6: # Simplistic threshold: saves overall work
                 message += "Automate this. This saves massive amounts of time."
             else:
                 message += "Don't automate this. This has very heavy costs."

             result_text.value = message
             page.update()

         page.add(
             ft.Text("ROI Automation Calculator", size=24, weight="bold"),
             ft.Column([
                 manual_time_input,
                 frequency_input,
                 coding_hours_input,
                 ft.ElevatedButton("Calculate ROI", on_click=calculate),
                 ft.Divider(),
                 result_text
             ], width=400, horizontal_alignment="center")
         )

     ft.app(target=main)
