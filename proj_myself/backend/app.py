from flask import Flask, jsonify, request, send_from_directory, session, Response
from pymongo import MongoClient
from pymongo.errors import BulkWriteError, ServerSelectionTimeoutError
import re
from werkzeug.utils import secure_filename
import os
from bson.binary import Binary
from flask import send_file
import io
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# Configure upload folder
UPLOAD_FOLDER = '../frontend/static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Connect to MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.server_info()  # Trigger exception if MongoDB is not reachable
    db = client['shopping_site']
    users_collection = db['users']
    license_keys_collection = db['license_keys']
    products_collection = db['products']

    # Ensure license keys exist in the database
    try:
        existing_keys = license_keys_collection.find({}, {"key": 1, "_id": 0})
        existing_keys_set = {key["key"] for key in existing_keys}

        license_keys_to_insert = [
            {"key": "ABC123", "active": True},
            {"key": "XYZ789", "active": True}
        ]

        keys_to_insert = [key for key in license_keys_to_insert if key["key"] not in existing_keys_set]

        if keys_to_insert:
            license_keys_collection.insert_many(keys_to_insert)
            print(f"Inserted license keys: {keys_to_insert}")
        else:
            print("License keys already exist in the database.")

    except BulkWriteError as e:
        print("Encountered an error during license key insertion:", e.details)

except ServerSelectionTimeoutError as e:
    print("Error: Unable to connect to MongoDB. Please ensure MongoDB is running.")
    exit(1)

# Pre-set admin accounts
admins = {
    "SDA1": "SDA999",
    "PDA1": "PDA999"
}

@app.route('/')
def serve_login():
    return send_from_directory('../frontend', 'index.html')

@app.route('/register')
def serve_register():
    return send_from_directory('../frontend', 'register.html')

@app.route('/home')
def serve_home():
    return send_from_directory('../frontend', 'home.html')

@app.route('/forget')
def serve_forget():
    return send_from_directory('../frontend', 'forget.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory('../frontend', path)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    license_code = data.get('license_code')

    print(f"Received registration data: {data}")  # Debugging log

    # Validate input fields
    if not username or not password or not confirm_password or not license_code:
        print("Error: Missing fields")  # Debugging log
        return jsonify({"error": "All fields are required"}), 400

    if password != confirm_password:
        print("Error: Passwords do not match")  # Debugging log
        return jsonify({"error": "Passwords do not match"}), 400

    # Validate license key
    license = license_keys_collection.find_one({"key": license_code, "active": True})
    if not license:
        print("Error: Invalid or inactive license key")  # Debugging log
        return jsonify({"error": "Invalid or inactive license code"}), 400

    # Check if username already exists
    if users_collection.find_one({"username": username}):
        print("Error: Username already exists")  # Debugging log
        return jsonify({"error": "Username already exists"}), 400

    # Insert the new user into the database
    try:
        users_collection.insert_one({"username": username, "password": password})
        license_keys_collection.update_one({"key": license_code}, {"$set": {"active": False}})
        print("Registration successful")  # Debugging log
        return jsonify({"message": "Registration successful"}), 201
    except Exception as e:
        print(f"Error during registration: {str(e)}")  # Debugging log
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    print(f"Received login data: {data}")  # Debugging log

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        print("Error: Missing username or password")  # Debugging log
        return jsonify({"error": "Username and password are required"}), 400

    user = users_collection.find_one({"username": username, "password": password})
    if not user:
        print("Error: Invalid username or password")  # Debugging log
        return jsonify({"error": "Invalid username or password"}), 401

    # Store the logged-in user's username in the session
    session['username'] = username
    print("Login successful")  # Debugging log
    return jsonify({"message": "Login successful"}), 200

@app.route('/api/login-admin', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username not in admins or admins[username] != password:
        return jsonify({"error": "Invalid admin credentials"}), 401

    # Simplify response without redirect logic
    return jsonify({"message": "Admin login successful"}), 200

@app.route('/sda')
def serve_sda():
    return send_from_directory('../frontend', 'sda.html')

@app.route('/pda')
def serve_pda():
    return send_from_directory('../frontend', 'pda.html')

@app.route('/add-product')
def serve_add_product():
    return send_from_directory('../frontend', 'add-product.html')

@app.route('/api/sda/users', methods=['GET'])
def get_users():
    users = list(users_collection.find({}, {"_id": 0, "username": 1, "password": 1, "email": 1, "address": 1}))
    return jsonify(users)

@app.route('/api/sda/users', methods=['DELETE'])
def delete_users():
    data = request.json
    usernames = data.get('usernames', [])
    if not usernames:
        return jsonify({"error": "No usernames provided"}), 400

    result = users_collection.delete_many({"username": {"$in": usernames}})
    return jsonify({"message": f"{result.deleted_count} user(s) deleted"}), 200

@app.route('/api/sda/users', methods=['PUT'])
def update_user():
    data = request.json
    original_username = data.get('originalUsername')  # Get the original username
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    address = data.get('address', '')

    if not original_username or not username or not password:
        return jsonify({"error": "Original username, new username, and password are required"}), 400

    # Update the user by matching the original username
    result = users_collection.update_one(
        {"username": original_username},
        {"$set": {"username": username, "password": password, "email": email, "address": address}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User updated successfully"})

@app.route('/api/sda/license-keys', methods=['GET', 'POST'])
def manage_license_keys():
    if request.method == 'GET':
        keys = list(license_keys_collection.find({}, {"_id": 0}))
        return jsonify(keys)

    if request.method == 'POST':
        data = request.json
        key = data.get('key')
        if not key:
            return jsonify({"error": "License key is required"}), 400
        license_keys_collection.insert_one({"key": key, "active": True})
        return jsonify({"message": "License key added"}), 201

@app.route('/api/sda/license-keys', methods=['PUT'])
def update_license_key():
    data = request.json
    original_key = data.get('originalKey')  # Get the original license key
    key = data.get('key')
    active = data.get('active')

    if not original_key or not key or active is None:
        return jsonify({"error": "Original key, new key, and active status are required"}), 400

    # Update the license key by matching the original key
    result = license_keys_collection.update_one(
        {"key": original_key},
        {"$set": {"key": key, "active": active}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "License key not found"}), 404

    return jsonify({"message": "License key updated successfully"}), 200

@app.route('/api/sda/license-keys', methods=['DELETE'])
def delete_license_keys():
    data = request.json
    keys = data.get('keys', [])
    if not keys:
        return jsonify({"error": "No license keys provided"}), 400

    result = license_keys_collection.delete_many({"key": {"$in": keys}})
    return jsonify({"message": f"{result.deleted_count} license key(s) deleted"}), 200

@app.route('/api/forget', methods=['POST'])
def forget_password():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    user = users_collection.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User found. Please reset your password."}), 200

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    username = data.get('username')
    new_password = data.get('newPassword')

    if not username or not new_password:
        return jsonify({"error": "Username and new password are required"}), 400

    result = users_collection.update_one({"username": username}, {"$set": {"password": new_password}})
    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "Password reset successful"}), 200

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        name = request.args.get('name')
        if name:
            product = products_collection.find_one({"name": name}, {"image": 0})
            if product:
                product["_id"] = str(product["_id"])
                product["image_url"] = f"/api/products/image/{product['_id']}"
                return jsonify({
                    "name": product["name"],
                    "category": product["category"],
                    "price": product["price"],
                    "inventory": product["inventory"],  # Updated field name
                    "description": product["description"],
                    "image_url": product["image_url"],
                    "code": product["code"]  # Include product code
                })
            else:
                return jsonify({"error": "Product not found"}), 404
        else:
            products = list(products_collection.find({}, {"image": 0}))
            for product in products:
                product["_id"] = str(product["_id"])
                product["image_url"] = f"/api/products/image/{product['_id']}"
            return jsonify(products)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/products', methods=['POST'])
def add_product():
    if 'image' not in request.files:
        return jsonify({"error": "Image is required"}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not image:
        return jsonify({"error": "Invalid image"}), 400

    # Convert image to binary
    image_binary = Binary(image.read())

    data = request.form
    name = data.get('name')
    category = data.get('category')
    price = data.get('price')
    quantity = data.get('quantity')
    description = data.get('description')

    # Validate all fields
    if not all([name, category, price, quantity, description]):
        return jsonify({"error": "All fields are required"}), 400

    # Generate the lowest available product code
    existing_codes = products_collection.distinct("code")
    existing_numbers = sorted(int(code.replace("product", "")) for code in existing_codes if code.startswith("product"))
    product_number = 1
    for number in existing_numbers:
        if number != product_number:
            break
        product_number += 1
    product_code = f"product{product_number}"

    try:
        # Store product with image binary in MongoDB
        product_id = products_collection.insert_one({
            "code": product_code,
            "image": image_binary,
            "name": name,
            "category": category,
            "price": float(price),
            "quantity": int(quantity),
            "description": description
        }).inserted_id
        return jsonify({"message": "Product added successfully", "product_id": str(product_id)}), 201
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/products/image/<product_id>', methods=['GET'])
def get_product_image(product_id):
    try:
        # Fetch the product by ID
        product = products_collection.find_one({"_id": ObjectId(product_id)})
        if not product or "image" not in product:
            return jsonify({"error": "Image not found"}), 404

        # Serve the image as a response
        return Response(
            product["image"],
            mimetype="image/jpeg"  # Adjust MIME type if necessary
        )
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/products/<product_code>', methods=['GET', 'PUT'])
def manage_product(product_code):
    if request.method == 'GET':
        product = products_collection.find_one({"code": product_code}, {"image": 0})
        if not product:
            return jsonify({"error": "Product not found"}), 404
        product["_id"] = str(product["_id"])
        return jsonify(product)

    if request.method == 'PUT':
        data = request.json
        update_fields = {
            "name": data.get("name"),
            "category": data.get("category"),
            "price": float(data.get("price")),
            "quantity": int(data.get("quantity")),
            "description": data.get("description")
        }
        result = products_collection.update_one({"code": product_code}, {"$set": update_fields})
        if result.matched_count == 0:
            return jsonify({"error": "Product not found"}), 404
        return jsonify({"message": "Product updated successfully"})

@app.route('/api/products/<product_code>', methods=['PUT'])
def update_product(product_code):
    try:
        data = request.json
        update_fields = {
            "name": data.get("name"),
            "category": data.get("category"),
            "price": float(data.get("price")),
            "quantity": int(data.get("quantity")),
            "description": data.get("description")
        }

        # Ensure all fields are provided
        if not all(update_fields.values()):
            return jsonify({"error": "All fields are required"}), 400

        # Locate the product by its code
        result = products_collection.update_one(
            {"code": product_code},
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({"message": "Product updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/products', methods=['DELETE'])
def delete_products():
    try:
        data = request.json
        product_ids = data.get('productIds', [])
        if not product_ids:
            return jsonify({"error": "No product IDs provided"}), 400

        result = products_collection.delete_many({"_id": {"$in": [ObjectId(pid) for pid in product_ids]}})
        return jsonify({"message": f"{result.deleted_count} product(s) deleted"}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/addlicense')
def serve_add_license():
    return send_from_directory('../frontend', 'addlicense.html')

@app.route('/api/sda/license-keys', methods=['POST'])
def add_license_key():
    data = request.json
    key = data.get('key')
    if not key:
        return jsonify({"error": "License key is required"}), 400

    # Add the new license key as active
    license_keys_collection.insert_one({"key": key, "active": True})
    return jsonify({"message": "License key added successfully"}), 201

@app.route('/user-info')
def serve_user_info():
    return send_from_directory('../frontend', 'user-info.html')

@app.route('/api/user-info', methods=['GET', 'PUT'])
def user_info():
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    current_username = session['username']  # Get the logged-in user's username

    if request.method == 'GET':
        user = users_collection.find_one({"username": current_username}, {"_id": 0})
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "username": user["username"],
            "password": user["password"],
            "email": user.get("email", ""),
            "address": user.get("address", "")
        })

    if request.method == 'PUT':
        data = request.json
        new_username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        address = data.get('address', '')

        if not new_username or not password:
            return jsonify({"error": "Username and password cannot be blank"}), 400

        if email and not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            return jsonify({"error": "Invalid email format"}), 400

        # Check if the new username already exists (excluding the current user)
        if new_username != current_username and users_collection.find_one({"username": new_username}):
            return jsonify({"error": "Username already exists"}), 400

        result = users_collection.update_one(
            {"username": current_username},
            {"$set": {"username": new_username, "password": password, "email": email, "address": address}}
        )

        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404

        # Update the session with the new username
        session['username'] = new_username

        return jsonify({"message": "User information updated successfully"})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Remove the username from the session
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/all-products')
def serve_all_products():
    return send_from_directory('../frontend', 'all-products.html')

@app.route('/search')
def serve_search():
    return send_from_directory('../frontend', 'search.html')

@app.route('/product-details')
def serve_product_details():
    return send_from_directory('../frontend', 'product-details.html')

# Wishlist routes
@app.route('/api/wishlist', methods=['POST'])
def add_to_wishlist():
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401
    
    data = request.json
    print(f"Received data: {data}")  # Debugging log to check received data
    product_code = data.get('product_code')  # Use product_code instead of product_id
    username = session['username']
    
    if not product_code:
        return jsonify({"error": "Product code is required"}), 400

    product = products_collection.find_one({"code": product_code})
    if not product:
        return jsonify({"error": "Product not found"}), 404

    wishlist_collection = db['wishlist']
    if wishlist_collection.find_one({"product_code": product_code, "username": username}):
        return jsonify({"error": "Product already in wishlist"}), 400

    wishlist_collection.insert_one({"product_code": product_code, "username": username})
    return jsonify({"message": "Product added to wishlist"}), 201

@app.route('/api/wishlist', methods=['GET'])
def get_wishlist():
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    username = session['username']
    wishlist_collection = db['wishlist']
    wishlist = list(wishlist_collection.find({"username": username}, {"_id": 0, "product_code": 1}))

    # Filter out documents without 'product_code'
    product_codes = [item['product_code'] for item in wishlist if 'product_code' in item]

    if not product_codes:
        return jsonify([])  # Return an empty list if no valid product codes are found

    products = list(products_collection.find({"code": {"$in": product_codes}}, {"image": 0}))
    for product in products:
        product["_id"] = str(product["_id"])
        product["image_url"] = f"/api/products/image/{product['_id']}"

    return jsonify(products)

@app.route('/api/wishlist', methods=['DELETE'])
def remove_from_wishlist():
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.json
    product_id = data.get('product_id')
    username = session['username']

    if not product_id:
        return jsonify({"error": "Product ID is required"}), 400

    wishlist_collection = db['wishlist']
    result = wishlist_collection.delete_one({"product_id": product_id, "username": username})

    if result.deleted_count == 0:
        return jsonify({"error": "Product not found in wishlist"}), 404

    return jsonify({"message": "Product removed from wishlist"}), 200

@app.route('/api/shopping-cart', methods=['GET', 'POST'])
def manage_cart():
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    username = session['username']
    cart_collection = db['shopping_cart']

    if request.method == 'GET':
        cart_items = list(cart_collection.find({"username": username}))
        for item in cart_items:
            product = products_collection.find_one({"code": item['product_code']})  # Use product_code
            if not product:
                continue  # Skip the cart item if the product is not found
            item['product'] = {
                "name": product['name'],
                "price": product['price']
            }
            item['_id'] = str(item['_id'])  # Convert ObjectId to string
        return jsonify(cart_items)

    if request.method == 'POST':
        data = request.json
        product_code = data.get('product_code')
        quantity = data.get('quantity')

        if not product_code or quantity is None:
            return jsonify({"error": "Product code and quantity are required"}), 400

        try:
            quantity = int(quantity)
            if quantity < 1:
                return jsonify({"error": "Quantity must be at least 1"}), 400
        except ValueError:
            return jsonify({"error": "Quantity must be a valid integer"}), 400

        product = products_collection.find_one({"code": product_code})
        if not product:
            return jsonify({"error": "Product not found"}), 404

        if quantity > product['inventory']:
            return jsonify({"error": f"Requested quantity exceeds available inventory ({product['inventory']})"}), 400

        cart_item = cart_collection.find_one({"username": username, "product_code": product_code})
        if cart_item:
            new_quantity = cart_item['quantity'] + quantity
            if new_quantity > product['inventory']:
                return jsonify({"error": f"Total quantity in cart exceeds available inventory ({product['inventory']})"}), 400
            cart_collection.update_one(
                {"_id": cart_item['_id']},
                {"$inc": {"quantity": quantity}}
            )
        else:
            cart_collection.insert_one({"username": username, "product_code": product_code, "quantity": quantity})

        return jsonify({"message": "Product added to cart"}), 201

@app.route('/api/shopping-cart/<item_id>', methods=['PUT', 'DELETE'])
def update_or_delete_cart_item(item_id):
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    username = session['username']
    cart_collection = db['shopping_cart']

    if request.method == 'PUT':
        data = request.json
        quantity = data.get('quantity')

        if not quantity or quantity < 1:
            return jsonify({"error": "Quantity must be at least 1"}), 400

        cart_collection.update_one(
            {"_id": ObjectId(item_id), "username": username},
            {"$set": {"quantity": quantity}}
        )
        return jsonify({"message": "Cart item updated"}), 200

    if request.method == 'DELETE':
        result = cart_collection.delete_one({"_id": ObjectId(item_id), "username": username})
        if result.deleted_count == 0:
            return jsonify({"error": "Cart item not found"}), 404
        return jsonify({"message": "Cart item deleted"}), 200

@app.route('/shopping-cart')
def serve_shopping_cart():
    return send_from_directory('../frontend', 'shopping-cart.html')

if __name__ == '__main__':
    app.run(debug=True)
