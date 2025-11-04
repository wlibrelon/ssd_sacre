from product import Product
import json
def generate_product():
    # list_product = []
    
    # for x in range(10):
    #     product = Product(
    #         name=f"Product {x+1}",
    #         price=10.0 * x,
    #         description=f"This is the description for product {x}"
    #     )
    #     list_product.append(product)
    # return list_product

    
    f = open("./Dados/products.json")
    data = json.loads(f.read())
    f.close()   
    # print("Dados carregados do JSON:", data)  # Diagnóstico
    return data

