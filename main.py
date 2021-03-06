#!/usr/bin/env python3.6

from flask import Flask, request, json
from sqlalchemy.ext.declarative import DeclarativeMeta

from database import db_session, Client, Product, init_db

app = Flask(__name__, static_url_path='/static/')
app.debug = True


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


SECRET = 'hunction2018'
VALIDATOR = 'ac8b63a1c41e75a214b6693a370ba4615962fce2'
EVENT_TYPE = 'DevicesSeen'
HARDCODED_MACS = [
    'bc:3d:85:23:4a:29',
    '94:65:2d:62:72:eb'
]

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)  # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/map.jpeg')
def mapAnswering():
    return app.send_static_file('map.jpeg')

@app.route('/init_db', methods=['POST'])
def initdb():
    if request.get_json()['secret'] == SECRET:
        init_db()

@app.route('/events', methods=['GET', 'POST'])
def events():
    if request.method == 'GET':
        return VALIDATOR, 200

    if not request.content_type == 'application/json':
        return 'Content-type must be application/json', 400

    map = request.get_json()

    if map['secret'] != SECRET:
        return 'Invalid request', 400

    if map['version'] != '2.0':
        print('invalid version:', map['version'])
        return 'Invalid request', 400

    if map['type'] != EVENT_TYPE:
        print('Incorrect event type:', map['type'])

    for c in map['data']['observations']:

        loc = c['location']
        if loc == None:
            continue
        name = c['clientMac']
        lat = loc['lat']
        lng = loc['lng']

        if name not in HARDCODED_MACS:
            continue

        client = Client.query.filter(Client.mac == name).first()
        if client == None:
            client = Client(name, lat, lng)
            print("holita crea el me.trexto")
            db_session.add(client)
        else:
            print("guardadito xd")
            client.lat = lat
            client.lng = lng

    db_session.commit()
    return "", 202


@app.route("/clients")
def getClients():
    clients = Client.query.all()
    clients = list(map(lambda x: x.getObject(), clients))
    return json.dumps(clients), 200, {'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}


@app.route("/clients/<secret>", methods=["DELETE"])
def deleteAll(secret):
    if secret == SECRET:
        Client.query.delete()
        return "Tot ha patat", 204
    else:
        return "No ha passat", 203


@app.route('/clients/<clientMac>')
def profile(clientMac):
    client = Client.query.filter(Client.mac == clientMac).first()
    return json.dumps(client, cls=AlchemyEncoder), 201, {'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}


@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == "GET":
        products = Product.query.all()
        products = list(map(lambda x: x.getObject(), products))
        return json.dumps(products), 200, {'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

    elif request.method == "POST":
        data = request.get_json()
        p = Product(lat=data["lat"], lng=data["lng"], order=data['order'], pl=data['placename'])
        db_session.add(p)
        db_session.commit()
        return json.dumps(p.getObject()), 201, {'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}


@app.route("/products/<productId>", methods=["DELETE"])
def delProduct(productId):
    product = Product.query.filter(Product.id == productId).first()
    if (product):
        db_session.delete(product)
        db_session.commit()
        return "", 204
    return "Product not found, hunctioner", 404


def main():
    app.run()


if __name__ == "__main__":
    main()
