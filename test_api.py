import requests

base_url = "http://127.0.0.1:8000"  # URL da API no servidor local

def test_get_product():
    # response = requests.get(f"{base_url}/{product_id}", params={"q": "example"})
    r = requests.get("http://127.0.0.1:8000/products")
    response = r.json()
    print("Resposta recebida da API:", response)  # Diagnóstico para validar a resposta JSON

    print(response)                 

    # assert response.status_code == 200
    # data = response.json()
    # assert data["id"] == product_id
    # assert "name" in data
    # assert "price" in data  

test_get_product()


# Testando o endpoint GET
# response = requests.get(f"{base_url}/42", params={"q": "teste"})

# Validando o status e a resposta
# if response.status_code == 200:
#     print("Resposta da API:", response.json())
# else:
#     print("Erro na requisição:", response.status_code)