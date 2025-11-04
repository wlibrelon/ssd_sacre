from fastapi.testclient import TestClient
from main import app  # Importe sua aplicação FastAPI
from pydantic import BaseModel # usado para criar classes de dados

client = TestClient(app)

# Testando um endpoint GET
def test_read_item():
    response = client.get("/items/42", params={"q": "teste"})
    assert response.status_code == 200
    assert response.json() == {"item_id": 42, "q": "teste"}

# Testando um endpoint POST
def test_create_item():
    data = {"name": "Notebook", "price": 3500.00, "description": "Laptop"}
    response = client.post("/items/", json=data)
    assert response.status_code == 200
    assert response.json() == {"message": "Item criado com sucesso!", "item": data}