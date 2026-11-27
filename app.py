from flask import Flask, render_template, jsonify, request
import uuid
import json

app = Flask(__name__)

categories = ("Accessories", "Computers", "Displays", "Audio", "Storage", "Networking")
order_statuses = ("Pending", "Confirmed", "Shipped", "Delivered", "Canceled")
payment_methods = ("Cash on Delivery", "Card")

def load_data():
    try:
        with open("storage.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"products": {}, "orders": []}
    return data

def save_data(data):
    with open("storage.json", "w") as f:
        json.dump(data,f, indent = 4)

@app.route("/")
def home():
    return render_template("index.html", categories=categories,statuses=order_statuses,payments=payment_methods)

@app.route("/api/products",methods=["GET"])
def view_products():
    data = load_data()
    return jsonify(data["products"])

@app.route("/api/products", methods = ["POST"])
def add_product():
    data = load_data()
    product = request.get_json()
    product_id = str(uuid.uuid4())

    if product["price"] <= 0 or product["stock"] < 0:
        return jsonify ({"message": "Invalid price or stock"}), 400

    if product["category"] not in categories:
        return jsonify({"message": "Invalid Category"}), 400
    data["products"][product_id] = product
    save_data(data)
    return jsonify({"message":"Product Added"}), 201

@app.route("/api/products/<product_id>", methods = ["PATCH"])
def update_product(product_id):
    data = load_data()
    products = data["products"]
    changes = request.get_json()

    if product_id not in products:
        return jsonify({"message": "Product not found"}), 404

    product = products[product_id].copy()
    for key,value in changes.items():
        if key in product:
            product[key] = value

    if product["price"] <= 0 or product["stock"] < 0:
        return jsonify({"message": "Invalid price or stock"}), 400
    if product["category"] not in categories:
        return jsonify({"message": "Invalid category"}), 400
    products[product_id] = product
    save_data(data)
    return jsonify({"message": "Product updated"})

@app.route("/api/products/<product_id>", methods = ["DELETE"])
def delete_product(product_id):
    data = load_data()
    if product_id not in data["products"]:
        return jsonify({"message": "Product not found"}), 404
    for order in data["orders"]:
        if order["product_id"] == product_id:
            if order["status"] not in ("Delivered", "Canceled"):
                return jsonify({"message": "Product has active orders"}), 400
    del data["products"][product_id]
    save_data(data)
    return jsonify({"message":"Product deleted"})

@app.route("/api/products/search", methods = ["GET"])
def search_products():
    data = load_data()
    query = request.args.get("q", "").lower()
    results = {}

    for key, value in data["products"].items():
        if query in value["name"].lower():
            results[key] = value
    return jsonify(results)

@app.route("/api/orders", methods = ["GET"])
def view_orders():
    data = load_data()
    return jsonify(data["orders"])

@app.route("/api/orders", methods = ["POST"])
def add_order():
    data = load_data()
    order = request.get_json()
    product_id = order["product_id"]
    quantity = order["quantity"]
    product = data["products"].get (product_id)
    if product is None:
        return jsonify({"message":"Product not found"}), 404
    if type(quantity) != int or quantity <= 0 or quantity > product["stock"]:
        return jsonify({"message":"Invalid quantity"}), 400
    if order["payment_method"] not in payment_methods:
        return jsonify({"message":"Invalid payment method"}), 400
    order["id"] = str(uuid.uuid4())
    order["product_name"] = product["name"]
    order["total"] = round(product["price"] * quantity, 2)
    order["status"] = order_statuses[0]
    product["stock"] -= quantity
    data["orders"].append(order)
    save_data(data)
    return jsonify ({"message": "Order added"}), 201

@app.route("/api/orders/<order_id>", methods = ["PATCH"])
def update_order(order_id):
    data = load_data()
    status = request.get_json()["status"]
    if status not in order_statuses:
        return jsonify({"message":"Invalid status"}), 400
    for order in data["orders"]:
        if order["id"] == order_id:
            if order["status"] in ("Delivered", "Canceled"):
                return jsonify({"message":"Order already closed"}), 400
            if status == "Canceled":
                product = data["products"].get(order["product_id"])
                if product is not None:
                    product["stock"] += order["quantity"]
            order["status"] = status
            save_data(data)
            return jsonify({"message":"order updated"})
    return jsonify({"message":"Order not found"}), 404

@app.route("/api/orders/<order_id>", methods = ["DELETE"])
def delete_order(order_id):
    data = load_data()
    orders = data["orders"]
    for i in range(len(orders)):
        if orders[i]["id"] == order_id:
            if orders[i]["status"] != "Canceled":
                return jsonify({"message":"Cancel order first"}), 400
            orders.pop(i)
            save_data(data)
            return jsonify({"message":"Order deleted"})
    return jsonify({"message":"Order not found"}), 404


if __name__ == "__main__":
    app.run(port = 5050, debug = True)