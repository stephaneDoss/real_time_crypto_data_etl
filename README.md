![Architecture du pipeline](Architecture\Architecture.png)
![Diagramme d'Architecture du pipeline](Architecture\Diagramme.png)

# Crypto Scraper Service

Ce projet permet de scraper les données des cryptomonnaies depuis CoinMarketCap et de les traiter en temps réel à l'aide de Kafka, Spark et MongoDB.

## Prérequis

- Docker
- Docker Compose

## Installation

1. Clonez le dépôt :

   ```sh
   git clone https://github.com/stephaneDoss/real_time_crypto_data_etl
   cd real_time_crypto_data_etl
   ```

2. Construisez et démarrez les services Docker :
   ```sh
   docker-compose up --build
   ```

## Services

### ZooKeeper

- **Image** : `confluentinc/cp-zookeeper:7.3.2`
- **Port** : `2181`

### Kafka

- **Image** : `confluentinc/cp-kafka:7.3.2`
- **Ports** : `9092`, `29092`
- **Topic** : `CryptoData`

### Spark Master

- **Image** : `bitnami/spark:latest`
- **Ports** : `6066`, `7077`, `8080`

### Spark Worker

- **Image** : `bitnami/spark:latest`
- **Ports** : `4040`
- **Volumes** : `./crypto_consumer.py:/opt/bitnami/spark/crypto_consumer.py`

### Spark Consumer

- **Image** : `bitnami/spark:latest`
- **Ports** : `4040`
- **Volumes** :
  - `./crypto_consumer.py:/opt/bitnami/spark/crypto_consumer.py`
  - `./mongo-spark-connector_2.13-10.2.1-javadoc.jar:/docker-entrypoint-initdb.d/mongo-spark-connector_2.13-10.2.1-javadoc.jar`
- **Command** :
  ```sh
  spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2,org.apache.kafka:kafka-clients:2.8.0,org.mongodb.spark:mongo-spark-connector_2.12:3.0.1 /opt/bitnami/spark/crypto_consumer.py
  ```

### Kafka Producer

- **Build** : `./Producer`
- **Volumes** : `./Producer:/app`

### Flask App

- **Build** : `./apiFlask`
- **Port** : `5000`

## Utilisation

1. Accédez à l'application Flask sur `http://localhost:5000`.
2. Les données des cryptomonnaies seront scrappées et traitées automatiquement.

## Structure du Projet

- `scrappingservice.py` : Contient la classe `CryptoScraper` pour scraper les données des cryptomonnaies.
- `docker-compose.yml` : Fichier de configuration Docker Compose pour orchestrer les différents services.
- `crypto_consumer.py` : Script Spark pour consommer les données de Kafka et les traiter.
- `Producer` : Répertoire contenant le code du producteur Kafka.
- `apiFlask` : Répertoire contenant le code de l application Flask.

## Auteurs

- [Stéphane DOSSOU](https://github.com/stephaneDoss)

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
