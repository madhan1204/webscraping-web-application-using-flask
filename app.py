from flask import Flask, render_template, request, redirect, url_for
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask import render_template
from flask import jsonify

app = Flask(__name__)

# Configure SQLAlchemy
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:madhan@localhost/webscrape'
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Base = declarative_base()

# Define a model for the shopping cart
class ShoppingCart(Base):
    __tablename__ = 'shopping_cart'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    price = Column(String)
    url = Column(String)

# Create the tables
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

def setup_driver():
    chrome_driver_path = "C://chromedriver//chromedriver.exe"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  # To run Chrome in headless mode
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_amazon(driver, query):
    amazon_url = f"https://www.amazon.in/s?k={query}"
    driver.get(amazon_url)
    time.sleep(5)  # Introduce a delay to ensure the page is fully loaded
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    products = []

    # Find all product elements in the search results
    product_elements = soup.find_all('div', {'data-component-type': 's-search-result'})

    for product in product_elements:
        title_element = product.find('span', class_='a-size-medium')
        price_element = product.find('span', class_='a-price-whole')
        url_element = product.find('a', class_='a-link-normal', href=True)

        if title_element and price_element and url_element:
            title = title_element.get_text().strip()
            price = price_element.get_text().strip()
            url = f"https://www.amazon.in{url_element['href']}"
            products.append({'title': title, 'price': price, 'url': url})

    return products

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form['query']
        driver = setup_driver()
        product_info = scrape_amazon(driver, query)
        driver.quit()  # Close the WebDriver session
        return render_template("index.html", product_info=product_info)
    return render_template("index.html")

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    # Retrieve item details from the request
    title = request.json.get('title')
    price = request.json.get('price')
    url = request.json.get('url')

    # Create a new ShoppingCart instance
    item = ShoppingCart(title=title, price=price, url=url)
    # Add the item to the session
    session.add(item)
    # Commit the transaction
    session.commit()

    # Send a JSON response indicating success
    return jsonify({"message": "Item added to cart successfully!"})

@app.route('/cart')
def view_cart():
    # Query the database to get all items in the shopping cart
    items = session.query(ShoppingCart).all()
    return render_template("cart.html", items=items)

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    # Retrieve item ID from the request
    item_id = request.json.get('id')

    # Remove the item from the database
    item = session.query(ShoppingCart).filter_by(id=item_id).first()
    if item:
        session.delete(item)
        session.commit()
        return jsonify({"message": "Item removed from cart successfully!"})
    else:
        return jsonify({"message": "Item not found in cart."}), 404


if __name__ == "__main__":
    app.run(debug=True)
