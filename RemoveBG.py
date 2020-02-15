import configparser
import logging
from io import BytesIO

import requests
from PIL import Image
from google_images_search import GoogleImagesSearch
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

config = configparser.ConfigParser()
config.read('token.ini')

token = str(config['DEFAULT']['token'])
gis = GoogleImagesSearch(str(config['DEFAULT']['google1']), str(config['DEFAULT']['google2']))
apiKey = str(config['DEFAULT']['removebgKey'])

updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


def start(update, context):
    # context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Bonjour. Envoie une photo avec un texte ("
                                                                    "caption) !")


def echo(update, context):
    file_id = update.message.photo[-1]
    newFile = context.bot.get_file(file_id)
    newFile.download('tmp')

    tmp_msg = "beach"
    if update.message.caption.strip() != "":
        tmp_msg = update.message.caption

    my_bytes_io = BytesIO()

    gis.search({'q': tmp_msg, 'num': 1, 'imgType': 'photo'})
    for image in gis.results():
        my_bytes_io.seek(0)
        raw_image_data = image.get_raw_data()
        image.copy_to(my_bytes_io)

    response = requests.post(
        'https://api.remove.bg/v1.0/removebg',
        files={'image_file': open('tmp', 'rb')},
        data={'size': 'auto'},
        headers={'X-Api-Key': apiKey},
    )

    if response.status_code == requests.codes.ok:
        with open('tmp', 'wb') as out:
            out.write(response.content)
    else:
        print("Error:", response.status_code, response.text)

    img = Image.open("tmp")
    background = Image.open(my_bytes_io)

    background = background.resize(img.size, Image.ANTIALIAS)

    background.paste(img, (0, 0), img)
    background.save('tmp', "PNG")
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('tmp', 'rb'))


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

echo_handler = MessageHandler(Filters.photo, echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()
