import schedule
import time
import winsound

# Set the alarm for 7:00 AM
schedule.every().day.at("07:00").do(winsound.Beep, 2500, 1000)

while True:
    schedule.run_pending()
    time.sleep(1)
