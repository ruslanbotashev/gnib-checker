from datetime import datetime
import syslog
import logging
import time
import json
import requests
import telebot

# configuration
START_DATE = datetime(2017, 10, 02, 00, 00, 00)
END_DATE = datetime(2017, 12, 5, 23, 59, 59)
BOT_TOKEN = '%telegram_bot_token%'  # telegram bot token
DESTINATION = '%telegram_destination_id%'  # telegram chat/group id
APPOINTMENT_TYPE = 'Renewal'  # either Renewal or New


URL = 'https://burghquayregistrationoffice.inis.gov.ie/Website/AMSREG/AMSRegWeb.nsf/(getAppsNear)?openpage&cat=Work&sbcat=All&typ={}'.format(APPOINTMENT_TYPE)
REQUEST_URL = '{url}&_={time}'
SLOT_FORMAT = '%d %B %Y - %H:%M'

def setup_logging():
    logger = logging.getLogger('gnib_checker')
    hdlr = logging.FileHandler('/var/log/gnib_checker.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

def main():
    bot = telebot.TeleBot(BOT_TOKEN)
    logger = setup_logging()
    sent_dates = []
    while True:
	time.sleep(5)
        dates_to_send = []
        try:
	    r = requests.get(REQUEST_URL.format(
                url=URL, time=time.time()), verify=False)
        except Exception:
            continue
        result = json.loads(r.content)
        if not result.get('slots'):
            logger.debug('No slots available')
            continue

        for slot in result['slots']:
            slot_date = datetime.strptime(slot['time'], SLOT_FORMAT)
            if slot_date > START_DATE and slot_date < END_DATE:
                dates_to_send.append(slot_date.strftime("%Y-%m-%d %H:%M"))

        if dates_to_send == sent_dates:
	    logger.debug('The same slots, not sending notification')
            continue

        if dates_to_send:
            message = 'Available slots found!\n{slots}'.format(
                slots='\n'.join(dates_to_send))
            try:
                bot.send_message(DESTINATION, message)
                logger.info(message)
            except Exception:
                continue
        sent_dates = dates_to_send

if __name__ == "__main__":
    main()
