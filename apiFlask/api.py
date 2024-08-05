from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['*'], expose_headers=['Content-Type'])
# Connexion à la base de données MongoDB
client = MongoClient("mongodb+srv://user:1234@cluster0.1t3thtv.mongodb.net/")
db = client['Crypto']
collection_price = db['price']

# Validité des intervalles de temps
VALID_TIMEFRAMES = ['10s', '1min', '5min',
                    '15min', '30min', '1h', '1d', '1w', '1m', '1y']


@app.route('/', methods=['GET'])
def home():
    print('Welcome to the Crypto API')
    return jsonify({'message': 'Welcome to the Crypto API'}), 200


@app.route('/cryptos/<crypto_symbol>/', methods=['GET'])
def get_crypto_data(crypto_symbol):
    # Récupération de l'intervalle de temps depuis les arguments de la requête
    timeframe = request.args.get('timeframe', default='1d')

    # Vérification de la validité de l'intervalle de temps
    if timeframe not in VALID_TIMEFRAMES:
        return jsonify({'error': 'Invalid timeframe parameter'}), 400

    # Configuration du fuseau horaire et de la date de début
    current_timezone = timezone.utc
    start_date = datetime.now()

    # Calcul de la date de début en fonction de l'intervalle de temps
    if timeframe == '10s':
        start_date -= timedelta(seconds=10)
    if timeframe == '1min':
        start_date -= timedelta(minutes=1)
    if timeframe == '15min':
        start_date -= timedelta(minutes=15)
    elif timeframe == '30min':
        start_date -= timedelta(minutes=30)
    elif timeframe == '1h':
        start_date -= timedelta(hours=1)
    elif timeframe == '1d':
        start_date -= timedelta(days=1)
    elif timeframe == '1w':
        start_date -= timedelta(weeks=1)
    elif timeframe == '1m':
        start_date -= timedelta(days=30)
    elif timeframe == '1y':
        start_date -= timedelta(days=365)

    # Conversion de la date de début en UTC
    start_date_utc = start_date.astimezone(current_timezone)

    # Récupération des données en fonction de l'intervalle de temps spécifié
    formatted_data = []
    if timeframe in ['10s', '1min', '5min', '15min', '30min', '1h', '1d', '1w']:
        formatted_data = get_data_for_fixed_intervals(
            crypto_symbol, start_date_utc, timeframe)
    elif timeframe in ['1m', '1y']:
        formatted_data = get_aggregated_data(
            crypto_symbol, start_date_utc, timeframe)

    # Sérialisation des données formatées en JSON
    serialized_data = json.dumps(formatted_data)
    return serialized_data, 200


def get_data_for_fixed_intervals(crypto_symbol, start_date_utc, timeframe):
    collection_name = f'aggregated_{timeframe}'
    delta = get_delta_for_interval(timeframe)

    # Récupération des données agrégées depuis MongoDB
    collection = db[collection_name]
    query = {'symbol': {"$eq": crypto_symbol}, 'window.start': {
        '$gte': start_date_utc - (delta * 10)}}
    projection = {'_id': 0, 'window.start': 1, 'avg_price': 1}
    data = list(collection.find(query, projection).sort(
        'window.start', -1).limit(10))

    # Formatage des données
    formatted_data = [{'date': entry['window']['start'].strftime(
        "%Y-%m-%d %H:%M:%S"), 'price': entry['avg_price']} for entry in data]
    return formatted_data


def get_aggregated_data(crypto_symbol, start_date_utc, timeframe):
    pipeline = []

    if timeframe == '1m':
        pipeline = [
            {
                '$match': {
                    'symbol': crypto_symbol,
                    'timestamp': {'$gte': start_date_utc - timedelta(days=30)}
                }
            },
            {
                '$group': {
                    '_id': {'$dateToString': {'format': '%Y-%m', 'date': '$timestamp'}},
                    'avg_price': {'$avg': '$price'}
                }
            },
            {'$sort': {'_id': 1}}
        ]
    elif timeframe == '1y':
        pipeline = [
            {
                '$match': {
                    'symbol': crypto_symbol,
                    'timestamp': {'$gte': start_date_utc}
                }
            },
            {
                '$group': {
                    '_id': {'$dateToString': {'format': '%Y', 'date': '$timestamp'}},
                    'avg_price': {'$avg': '$price'}
                }
            },
            {'$sort': {'_id': 1}}
        ]

    # Récupération des données agrégées depuis MongoDB
    result = list(collection_price.aggregate(pipeline))

    # Formatage des données
    formatted_data = [{'day': entry['_id'],
                       'price': entry['avg_price']} for entry in result]
    return formatted_data


def get_delta_for_interval(timeframe):
    if timeframe == '10s':
        return timedelta(seconds=10)
    if timeframe == '1min':
        return timedelta(minutes=1)
    if timeframe == '5min':
        return timedelta(minutes=5)
    if timeframe == '15min':
        return timedelta(minutes=15)
    elif timeframe == '30min':
        return timedelta(minutes=30)
    elif timeframe == '1h':
        return timedelta(hours=1)
    elif timeframe == '1d':
        return timedelta(days=1)
    elif timeframe == '1w':
        return timedelta(weeks=1)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


# from flask import Flask, request, jsonify
# from pymongo import MongoClient
# from datetime import datetime, timedelta, timezone
# import json
# from kafka import KafkaConsumer

# app = Flask(__name__)

# # Connexion à la base de données MongoDB
# client = MongoClient("mongodb+srv://user:1234@cluster0.1t3thtv.mongodb.net/")
# db = client['Crypto']
# collection_price = db['price']

# # Connexion à Kafka pour consommer les données agrégées
# consumer = KafkaConsumer(
#     'Price',
#     bootstrap_servers=['69.48.186.31:9092'],
#     auto_offset_reset='latest',
#     enable_auto_commit=False,
#     group_id='my-group'
# )

# # Validité des intervalles de temps
# VALID_TIMEFRAMES = ['10s', '1min', '15min', '30min', '1h', '1d', '1w', '1m', '1y']


# @app.route('/', methods=['GET'])
# def home():
#     print('Welcome to the Crypto API')
#     return jsonify({'message': 'Welcome to the Crypto API'}), 200


# @app.route('/cryptos/<crypto_symbol>/', methods=['GET'])
# def get_crypto_data(crypto_symbol):
#     # Récupération de l'intervalle de temps depuis les arguments de la requête
#     timeframe = request.args.get('timeframe', default='1d')

#     # Vérification de la validité de l'intervalle de temps
#     if timeframe not in VALID_TIMEFRAMES:
#         return jsonify({'error': 'Invalid timeframe parameter'}), 400

#     # Configuration du fuseau horaire et de la date de début
#     current_timezone = timezone.utc
#     start_date = datetime.now()

#     # Calcul de la date de début en fonction de l'intervalle de temps
#     if timeframe == '10s':
#         # Consommer les données de Kafka pour l'intervalle de temps de 10 secondes
#         formatted_data = consume_kafka_data('10s')
#     elif timeframe == '1min':
#         # Consommer les données de Kafka pour l'intervalle de temps de 1 minute
#         formatted_data = consume_kafka_data('1min')
#     else:
#         start_date -= get_delta_for_interval(timeframe)
#         start_date_utc = start_date.astimezone(current_timezone)
#         if timeframe in ['15min', '30min', '1h', '1d', '1w']:
#             formatted_data = get_data_for_fixed_intervals(
#                 crypto_symbol, start_date_utc, timeframe)
#         elif timeframe in ['1m', '1y']:
#             formatted_data = get_aggregated_data(
#                 crypto_symbol, start_date_utc, timeframe)

#     # Sérialisation des données formatées en JSON
#     serialized_data = json.dumps(formatted_data)
#     return serialized_data, 200


# def consume_kafka_data(interval):
#     data = []
#     if interval == '10s':
#         # Consommer les données de Kafka pour l'intervalle de temps de 10 secondes
#         for message in consumer:
#             data.append(json.loads(message.value.decode('utf-8')))
#             if len(data) >= 10:  # Arrêter après avoir consommé 10 messages
#                 break
#     elif interval == '1min':
#         # Consommer les données de Kafka pour l'intervalle de temps de 1 minute
#         for message in consumer:
#             data.append(json.loads(message.value.decode('utf-8')))
#             if len(data) >= 60:  # Arrêter après avoir consommé 60 messages (1 par seconde)
#                 break
#     return data


# def get_data_for_fixed_intervals(crypto_symbol, start_date_utc, timeframe):
#     collection_name = f'aggregated_{timeframe}'
#     delta = get_delta_for_interval(timeframe)

#     # Récupération des données agrégées depuis MongoDB
#     collection = db[collection_name]
#     query = {'symbol': {"$eq": crypto_symbol}, 'window.start': {
#         '$gte': start_date_utc - (delta * 10)}}
#     projection = {'_id': 0, 'window.start': 1, 'avg_price': 1}
#     data = list(collection.find(query, projection).sort(
#         'window.start', -1).limit(10))

#     # Formatage des données
#     formatted_data = [{'date': entry['window']['start'].strftime(
#         "%Y-%m-%d %H:%M:%S"), 'price': entry['avg_price']} for entry in data]
#     return formatted_data


# def get_aggregated_data(crypto_symbol, start_date_utc, timeframe):
#     pipeline = []

#     if timeframe == '1m':
#         pipeline = [
#             {
#                 '$match': {
#                     'symbol': crypto_symbol,
#                     'timestamp': {'$gte': start_date_utc - timedelta(days=30)}
#                 }
#             },
#             {
#                 '$group': {
#                     '_id': {'$dateToString': {'format': '%Y-%m', 'date': '$timestamp'}},
#                     'avg_price': {'$avg': '$price'}
#                 }
#             },
#             {'$sort': {'_id': 1}}
#         ]
#     elif timeframe == '1y':
#         pipeline = [
#             {
#                 '$match': {
#                     'symbol': crypto_symbol,
#                     'timestamp': {'$gte': start_date_utc}
#                 }
#             },
#             {
#                 '$group': {
#                     '_id': {'$dateToString': {'format': '%Y', 'date': '$timestamp'}},
#                     'avg_price': {'$avg': '$price'}
#                 }
#             },
#             {'$sort': {'_id': 1}}
#         ]

#     # Récupération des données agrégées depuis MongoDB
#     result = list(collection_price.aggregate(pipeline))

#     # Formatage des données
#     formatted_data = [{'day': entry['_id'],
#                        'price': entry['avg_price']} for entry in result]
#     return formatted_data


# def get_delta_for_interval(timeframe):
#     if timeframe == '10s':
#         return timedelta(seconds=10)
#     elif timeframe == '1min':
#         return timedelta(minutes=1)
#     elif timeframe == '15min':
#         return timedelta(minutes=15)
#     elif timeframe == '30min':
#         return timedelta(minutes=30)
#     elif timeframe == '1h':
#         return timedelta(hours=1)
#     elif timeframe == '1d':
#         return timedelta(days=1)
#     elif timeframe == '1w':
#         return timedelta(weeks=1)
#     elif timeframe == '1m':
#         return timedelta(days=30)
#     elif timeframe == '1y':
#         return timedelta(days=365)


# if __name__ == '__main__':
#     # Démarrer l'API Flask
#     app.run(debug=True)
