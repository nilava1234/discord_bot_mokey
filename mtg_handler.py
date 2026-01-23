from mtgsdk import Card, Set, Type, Supertype, Subtype, Changelog
from PIL import Image
from io import BytesIO
import requests
import discord

# Function to fetch MTG cards by name
def fetch_cards_by_name(name):
    
    card_details = {}
    try:
        cards = Card.where(name=name).all()
        card = cards[0]
        url = f"https://api.scryfall.com/cards/named?fuzzy={card.name}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            card_details = {
                "name": card.name,
                "disc": card.text,
                "image_url": card.image_url,
                "price": data['prices']['usd'] if data['prices']['usd'] else "-00.00",
                "legal": any(legality['format'] == 'Commander' and legality['legality'] == 'Legal' for legality in card.legalities)
            }



    except Exception as e:
        print(f"Exception Thrown   \\/ \n{e}")
        url = f"https://api.scryfall.com/cards/named?fuzzy={name}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            card_details = {
                "name": data['name'],
                "disc": data['oracle_text'],
                "image_url": data['image_uris']['normal'] if 'image_uris' in data else "Image not available.",
                "price": data['prices']['usd'] if data['prices']['usd'] else "-00.00",
                "legal": True if data['legalities'].get('commander', None) == 'legal' else False
            }
        else:
            return None
    return card_details
            
def fetch_cards_by_effect(key):
    cards = Card.where()
# Function to display images

async def display_cards(ctx, card_details):
    # card = cards[0]
    print(card_details['name'])
    # await ctx.channel.send(
    #     f"**Name:{card_details['name']}**\n"
    #     f"Discription:\n {card_details['disc']}\n\n"
    #     f"Average cost: ***${card_details['price']}***\n"
    #     f"Commander Legal: {'✅' if card_details['legal'] else '❌'}\n"
    #     f"{card_details['image_url']}"
    # )
    embed = discord.Embed(title=f"**Name: {card_details['name']}**", color=discord.Color.blue())
    embed.add_field(name="Description", value=card_details['disc'], inline=False)
    embed.add_field(name="Average cost", value=f"***${card_details['price']}***", inline=False)
    embed.add_field(name="Commander Legal", value='✅' if card_details['legal'] else '❌', inline=False)
    embed.set_image(url=card_details['image_url'])

    await ctx.channel.send(embed=embed)

        
# Main function to display cards based on user choice
async def mtg_main(ctx, input):
    print(input)
    await ctx.response.send_message(f"Looking up \"{input}\" ...")
    card_detials = fetch_cards_by_name(input)
    if card_detials != None:
        await display_cards(ctx, card_detials)
    else:
        print("Look up failed")
        await ctx.channel.send("Look up failed... Card not found")