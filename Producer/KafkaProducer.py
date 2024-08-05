import os
import json
import time
from confluent_kafka import Producer
from ScrappingService import CryptoScraper
from utils import initLogger

# Initialisation du logger
LOGGER = initLogger("KAFKA_PRODUCER_LOG")

# Récupération des configurations depuis les variables d'environnement
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka1:19092')

# Initialisation du producteur Kafka
producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})


def produceMessage(data):
    """
    Envoie un message au topic Kafka 'CryptoData'.

    Args:
        data (dict): Les données de la cryptomonnaie à envoyer.
    """
    producer.produce('CryptoData', value=json.dumps(data).encode('utf-8'))
    LOGGER.info("Messages produits vers le topic Kafka : CryptoData")
    producer.flush()


if __name__ == "__main__":
    # Initialisation du scraper
    scrapping = CryptoScraper()

    while True:
        # Récupération des données des cryptomonnaies
        bitcoin = scrapping.get_data('Bitcoin')
        ethereum = scrapping.get_data('Ethereum')
        xrp = scrapping.get_data('XRP')

        # Envoi des données à Kafka
        if bitcoin:
            produceMessage(bitcoin)
        if ethereum:
            produceMessage(ethereum)
        if xrp:
            produceMessage(xrp)

        # Pause de 10 secondes entre chaque scrap
        time.sleep(10)
