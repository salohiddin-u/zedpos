from google import genai
from google.genai import types

import anthropic

from PIL import Image

import base64

import os
import django

from environs import Env

env = Env()
env.read_env()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'config.settings')
django.setup()

from pos.models import *

client = anthropic.Anthropic(api_key=env.str("API_KEY"))

def ai_handler():
#     img = Image.open("saved_image.jpg")
#     img.thumbnail((1200, 1200))
#     img.save("resized.jpg", quality=90)
#     with open("resized.jpg", 'rb') as f:
#         image_data = base64.standard_b64encode(f.read()).decode("utf-8")
#     products = list(Product.objects.filter().values_list("name", flat=True))
#     products_str = "\n".join(products)
#     prompt = f"""products:
# {products_str}

# Match each scanned item on the invoice to its closest product name from the list above (fuzzy match, handle typos/abbreviations/Cyrillic→Latin). If no reasonable match exists, set name to null. Extract the quantity for each item from the image."""

#     response = client.messages.create(
#         model="claude-opus-5",
#         max_tokens=1000,
#         thinking={"type": "disabled"},
#         tools=[
#             {
#                 "name": "record_matches",
#                 "description": "Record the matched products with quantities from the scanned invoice",
#                 "input_schema": {
#                     "type": "object",
#                     "properties": {
#                         "items": {
#                             "type": "array",
#                             "items": {
#                                 "type": "object",
#                                 "properties": {
#                                     "name": {
#                                         "type": ["string", "null"],
#                                         "description": "The exact matched product name from the provided list, or null if no reasonable match exists"
#                                     },
#                                     "qty": {
#                                         "type": "number",
#                                         "description": "The quantity shown on the invoice for this item"
#                                     }
#                                 },
#                                 "required": ["name", "qty"]
#                             }
#                         }
#                     },
#                     "required": ["items"]
#                 }
#             }
#         ],
#         tool_choice={"type": "tool", "name": "record_matches"},
#         messages=[
#             {
#                 "role": "user",
#                 "content": [
#                     {
#                         "type": "image",
#                         "source": {
#                             "type": "base64",
#                             "media_type": "image/jpeg",
#                             "data": image_data
#                         }
#                     },
#                     {
#                         "type": "text",
#                         "text": prompt
#                     }
#                 ]
#             }
#         ]
#     )

#     tool_use_block = next(b for b in response.content if b.type == "tool_use")
    # return tool_use_block.input["items"]
    return [{'id':1, 'name': 'Pepsi 2l', 'qty': 18, 'status': "matched"}, 
            {'id':2, 'name': 'Pepsi 1.5l', 'qty': 12, 'status': "matched"}, 
            {'id':3, 'name': 'Pepsi 1l', 'qty': 24, 'status': "matched"}, 
            {'id':4, 'name': 'Pepsi 0.5l', 'qty': 24, 'status': "matched"}, 
            {'id':5, 'name': 'Pepsi 0.45l', 'qty': 24, 'status': "matched"}, 
            {'id':6, 'name': 'Lipton 1.5l limon', 'qty': 6, 'status': "matched"}, 
            {'id':7, 'name': 'Lipton 1l limon', 'qty': 6, 'status': "matched"}]

