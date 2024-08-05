import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

# URL de la page à scraper
URL = "https://coinmarketcap.com/"


def currentUnixTime():
    """
    Retourne l'heure actuelle en temps Unix.

    Returns:
        int: Temps Unix actuel.
    """
    return int(round(time.time()))


class CryptoScraper:
    """
    Classe pour scraper les données des cryptomonnaies depuis CoinMarketCap.
    """

    def __init__(self):
        """
        Initialise l'instance de CryptoScraper avec l'URL par défaut de CoinMarketCap.
        """
        self.URL = "https://coinmarketcap.com/"

    def get_data(self, crypto_name):
        """
        Scrape les données pour une cryptomonnaie spécifique.

        Args:
            crypto_name (str): Le nom de la cryptomonnaie à scraper.

        Returns:
            dict: Les données de la cryptomonnaie scrappée, ou None si non trouvée.
        """
        # Envoi de la requête HTTP à l'URL
        response = requests.get(self.URL)
        soup = BeautifulSoup(response.text, "html.parser")

        # Recherche du tableau des cryptomonnaies
        contentTable = soup.find('table')
        contentBody = contentTable.find('tbody')
        rows = contentBody.find_all('tr')

        # Obtention de la date et heure actuelle
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Parcours de chaque ligne du tableau pour trouver la cryptomonnaie
        for tr in rows:
            td_elements = tr.find_all('td')
            crypto_name_element = td_elements[2]
            current_crypto_name = crypto_name_element.find(
                'div').find('a').find('div').find('p').text.strip()

            if current_crypto_name.lower() != crypto_name.lower():
                continue

            # Extraction des informations de la cryptomonnaie
            crypto_logo = crypto_name_element.find('div').find(
                'a').find('div').find('img').get('src')

            crypto_price_element = td_elements[3]
            crypto_price = crypto_price_element.find('span').text.strip()
            prix_cleaned = re.sub(r'[^\d.-]', '', crypto_price)
            try:
                prix_decimal = float(prix_cleaned)
            except ValueError:
                prix_decimal = 0

            crypto_variation_1h_element = td_elements[4]
            crypto_variation_1h = crypto_variation_1h_element.find(
                'span').text.strip()
            variation_1h = crypto_variation_1h.replace('%', '')
            try:
                variation_1h_decimal = float(variation_1h)
            except ValueError:
                variation_1h_decimal = 0

            crypto_variation_24h_element = td_elements[5]
            crypto_variation_24h = crypto_variation_24h_element.find(
                'span').text.strip()
            variation_24h = crypto_variation_24h.replace('%', '')
            try:
                variation_24h_decimal = float(variation_24h)
            except ValueError:
                variation_24h_decimal = 0

            crypto_variation_7d_element = td_elements[6]
            crypto_variation_7d = crypto_variation_7d_element.find(
                'span').text.strip()
            variation_7d = crypto_variation_7d.replace('%', '')
            try:
                variation_7d_decimal = float(variation_7d)
            except ValueError:
                variation_7d_decimal = 0

            crypto_market_cap_element = td_elements[7]
            crypto_market_cap_all = crypto_market_cap_element.find_all('span')
            crypto_market_cap_long = crypto_market_cap_all[1].text.strip()
            capitalisation_boursiere = crypto_market_cap_long.replace(
                ',', '').replace('$', '')
            try:
                capitalisation_boursiere_decimal = float(
                    capitalisation_boursiere)
            except ValueError:
                capitalisation_boursiere_decimal = 0

            crypto_volume_24h_element = td_elements[8]
            crypto_volume_24h = crypto_volume_24h_element.find(
                'div').find('a').find('p').text.strip()
            volume_24h_cleaned = re.sub(r'[^\d.]', '', crypto_volume_24h)
            if volume_24h_cleaned:
                volume_24h_decimal = float(volume_24h_cleaned)
            else:
                volume_24h_decimal = 0

            # Dictionnaire contenant les informations de la cryptomonnaie
            crypto_info = {
                "symbol": current_crypto_name,
                "logo": crypto_logo,
                "price": prix_decimal,
                "variation_1h": variation_1h_decimal,
                "variation_24h": variation_24h_decimal,
                "variation_7d": variation_7d_decimal,
                "Capitalisation boursière": capitalisation_boursiere_decimal,
                "volume": volume_24h_decimal,
                "timestamp": current_datetime  # Ajout de la date au format ISO 8601
            }

            return crypto_info

        return None
