from fastapi import FastAPI
from indb import generate_product
from product import Product
from SSD_SACRE.jsondb import JsonDB

app = FastAPI()
productDB = JsonDB(filepath="./Dados/products.json")

#products = generate_product()

@app.get("/products")
def get_products():
    products = productDB.read_data()
    return {"Produtos": products}

@app.post("/products")
def create_products(product: Product):
    print("Produto recebido:", product)  # Diagnóstico para validar o produto recebido
    productDB.append(product)  # Adiciona o produto à lista como dicionário   
    return {"Produtos": "Inserido"}