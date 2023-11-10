from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import requests

app = Flask(__name__)

# Configuración de la base de datos

#Para la base de datos local
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mypassword@localhost:3306/flaskmysql'

#Para la base de datos en docker
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mypassword@mysql:3306/flaskmysql'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Modelo de datos
class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(200))

    def __init__(self, data):
        self.data = data
        
with app.app_context():
    db.create_all()

# Esquema (schema) para el modelo Data
class DataSchema(ma.Schema):
    class Meta:
        fields = ('id', 'data')

data_schema = DataSchema()
data_schemas = DataSchema(many=True)

# Ruta para obtener datos del servicio externo
@app.route('/api/data', methods=['GET'])
def get_data():
    response = requests.get('https://restcountries.com/v3.1/all')
    
    if response.status_code == 200:
        data = response.json()
        countries_data = []
        for country in data:
            country_data = {
                "Nombre Pais": country.get('name', {}).get('common', '') ,
            }
            countries_data.append(country_data)

        return jsonify(countries_data)
    else:
        return jsonify({"message": "No se pudieron obtener datos del servicio externo"}, 500)

# Ruta para almacenar datos en la base de datos

@app.route('/api/data', methods=['POST'])
def store_data():
    try:
        response = requests.get('https://restcountries.com/v3.1/all')

        if response.status_code == 200:
            data = response.json()
            countries_data = []
            for country in data:
                country_name = country.get('name', {}).get('common', '')
                if country_name:
                    new_data = Data(data=country_name)
                    db.session.add(new_data)
                    countries_data.append({"Nombre Pais": country_name})

            db.session.commit()

            # Serializar las nuevas entradas con el esquema DataSchema
            results = data_schemas.dump(countries_data)
            return jsonify({"message": "Datos almacenados exitosamente", "data": countries_data})
        else:
            return jsonify({"message": "No se pudieron obtener datos del servicio externo"}, 500)
    except Exception as e:
        return jsonify({"message": f"Error al almacenar datos: {str(e)}"}, 500)


# Ruta para obtener un registro específico por ID
@app.route('/api/data/<int:id>', methods=['GET'])
def get_data_by_id(id):
    data = Data.query.get(id)
    if data:
        return jsonify(data_schema.dump(data))
    else:
        return jsonify({"message": "Registro no encontrado"}, 404)

if __name__ == '__main__':
    app.run(debug=True)