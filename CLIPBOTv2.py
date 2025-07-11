import re
import requests
import json
import os
from irc import client

CONFIG_FILE = "config_clipbot.json"
clip_regex = re.compile(r"https:\/\/www\.twitch\.tv\/([a-zA-Z0-9_]+)\/clip\/([a-zA-Z0-9\-]+)")

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def load_config():
    if not os.path.isfile(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def ask_config():
    print("\n=== Configuration du bot ===")
    TWITCH_NICK = input("Entrez le nom du compte Twitch utilisé (TWITCH_NICK) : ").strip()
    raw_token = input("Entrez le token Twitch (exemple: oauth:xxxx ou juste xxxxx) : ").strip()
    # Ajoute automatiquement 'oauth:' si manquant
    TWITCH_TOKEN = raw_token if raw_token.startswith("oauth:") else "oauth:" + raw_token
    TWITCH_CHANNEL = input("Chaîne Twitch à écouter (ex: sebwellz) : ").strip()
    DISCORD_WEBHOOK_URL = input("Lien Webhook Discord : ").strip()
    config = {
        "TWITCH_NICK": TWITCH_NICK,
        "TWITCH_TOKEN": TWITCH_TOKEN,
        "TWITCH_CHANNEL": TWITCH_CHANNEL,
        "DISCORD_WEBHOOK_URL": DISCORD_WEBHOOK_URL
    }
    save_config(config)
    print("Configuration enregistrée.")
    return config

def menu_config():
    while True:
        print("\nConfiguration existante détectée.")
        print("[1] Utiliser la configuration enregistrée (Remember)")
        print("[2] Modifier la configuration")
        print("[3] Supprimer la configuration et quitter")
        choix = input("Choix : ").strip()
        if choix == "1":
            config = load_config()
            return config
        elif choix == "2":
            config = ask_config()
            return config
        elif choix == "3":
            os.remove(CONFIG_FILE)
            print("Configuration supprimée. Relancez le programme pour reconfigurer.")
            exit()
        else:
            print("Choix invalide, recommence.")

def send_to_discord(webhook_url, channel_name, msg):
    data = {"content": f"🎬 Nouveau clip : {msg}"}
    try:
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"Erreur lors de l'envoi sur Discord : {e}")

def main():
    config = load_config()
    if config:
        config = menu_config()
    else:
        config = ask_config()
        print("\nConfiguration enregistrée. Relancez simplement le programme pour démarrer le bot.\n")
        exit()

    print("Lancement du bot.\n")
    TWITCH_CHANNEL = config["TWITCH_CHANNEL"].lower()

    def on_pubmsg(connection, event):
        msg = event.arguments[0]
        match = clip_regex.search(msg)
        if match:
            channel = match.group(1).lower()
            if channel == TWITCH_CHANNEL:
                print(f"Clip détecté pour la chaîne {channel}: {msg}")
                send_to_discord(config["DISCORD_WEBHOOK_URL"], channel, msg)

    reactor = client.Reactor()
    try:
        c = reactor.server().connect(
            "irc.chat.twitch.tv",
            6667,
            config["TWITCH_NICK"],
            password=config["TWITCH_TOKEN"]
        )
    except client.ServerConnectionError:
        print("Impossible de se connecter à Twitch IRC")
        return

    c.add_global_handler("pubmsg", on_pubmsg)
    c.join(f"#{config['TWITCH_CHANNEL']}")
    print(f"Bot prêt sur #{config['TWITCH_CHANNEL']} (ctrl+c pour quitter)")
    reactor.process_forever()

if __name__ == "__main__":
    main()
