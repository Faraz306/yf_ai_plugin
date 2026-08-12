import flet as ft

class MyApp(ft.UserControl):
    def __init__(self):
        super().__init__()        
        self.history = ft.Text(value='')
        self.predict = ft.Text(value='')
        self.button = ft.ElevatedButton("Predict")
        self.email_button = ft.ElevatedButton("Send Email")

        self.controls = [self.history, self.predict, self.button, self.email_button]

        self.button.on_click = self.calculate_roi

    def calculate_roi(self, e):
        # TO DO: implement the prediction logic here
        self.predict.value = "Patient will come to the hospital"

        # Send email if patient will not come
        if self.predict.value == "Patient will not come to the hospital":
            # TO DO: implement email sending logic here
            print("Email sent to patient")

        # Notify hospital
        print("Notifying hospital")

    def build(self):
        return ft.Column(
            [ft.Text("Patient History")],
            [self.history],
            [ft.Text("Prediction")],
            [self.predict],
            [self.button],
            [self.email_button]
        )

def main(page):
    app = MyApp()
    page.add(app)
    page.update()
    ft.app(target=main)
