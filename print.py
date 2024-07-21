from escpos.printer import Usb
import requests
import textwrap
import sys
import json

if (len(sys.argv) < 2):
	print("Please supply a deck to print")
	exit(1)

def cardNum(num):
	return "?" if num == -1 else str(num)
def cardType(type):
	return {
		"standardSpell": "Standard Spell",
		"continuousSpell": "Continuous Spell",
		"enchantSpell": "Enchant Spell",
		"standardItem": "Standard Item",
		"continuousItem": "Continuous Item",
		"equipableItem": "Equipable Item"
	}[type]
def cardName(name):
	return name if len(name) <= 33 else name[:30].strip() + "..."
def textReplacements(text):
	text = text.replace("　", "")
	text = text.replace("［", "[")
	text = text.replace("］", "]")
	text = text.replace("※", "*")
	return text

def cardToPrintout(card):
	out = ""
	
	# Write name
	out += f"╔═{cardName(card['name']).ljust(33, '═')}═Lv{cardNum(card['level']).rjust(2)}═╗"
	
	# Determine effect box size
	effectText = ""
	currentEffect = 1
	for effect in card["effects"]:
		text = textReplacements(effect["text"])
		
		if text.startswith("●："):
			text = text.replace("●：", str(currentEffect) + ":", 1)
			currentEffect += 1
		
		currentSubEffect = 97 # lower case A
		while "●" in text:
			if ("●：" in text):
				text = text.replace("●：", chr(currentSubEffect) + ":", 1)
			else: # must be able to deal with "●1,2："
				text = text.replace("●", chr(currentSubEffect) + "(", 1)
				text = text.replace("：", "):", 1)
			currentSubEffect += 1
		
		effectText += " " + text
	if (len(card["effects"]) == 0): # only flavor text
		effectText = " " + textReplacements(card["effectsPlain"])
	
	effectText = effectText[1:] # cut off leading space
	effectLines = textwrap.wrap(effectText, width=40);
	
	# Write image space
	for _ in range(18 - len(effectLines)):
		out += "\n║                                        ║"
	
	# Write types
	if len(','.join(card['types'])) > 38:
		print(f"Cannot print '{card['name']}' because it has too many types.")
		exit(2)
	out += f"\n╠═{','.join(card['types']).ljust(38, '═')}═╣"
	
	# Write effects
	for line in effectLines:
		out += f"\n║{line.ljust(40)}║"
	
	if card["cardType"] in ["unit", "token"]:
		out += f"\n╚═Attack:{cardNum(card['attack']).rjust(4)}═══════════════Defense:{cardNum(card['defense']).rjust(4)}═╝"
	else:
		out += f"\n╚{cardType(card['cardType']).center(40, '═')}╝"
	
	return out

print("Reading deck...")
file = open(sys.argv[1], encoding="utf8")
deck = json.load(file)
file.close()

print("Loading card data...")
cards = requests.post("https://crossuniverse.net/cardInfo", json={}).json()

partner = next(c for c in cards if c["cardID"] == deck["Partner"][2:])
deckCards = []
for cardId in deck["Cards"]:
	deckCards.append(next(c for c in cards if c["cardID"] == cardId[2:]))

print("Printing deck...")
printer = Usb(0x0416, 0xAABB, 0, profile="POS-5890")
printer.set(font="b")
printer.text(cardToPrintout(partner))
for card in deckCards:
	printer.text(f"\n  {'─' * 38}  \n")
	printer.text(cardToPrintout(card))

printer.ln(4)