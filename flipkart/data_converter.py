import pandas as pd
from langchain_core.documents import Document
import os

def dataconverter():
    # Get absolute path to data file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(os.path.dirname(current_dir), "data", "flipkart_product_review.csv")
    
    # Read the CSV file
    product_data = pd.read_csv(data_path)

    # Select relevant columns
    data = product_data[["product_title", "review", "rating", "summary"]]

    product_list = []

    # Iterate over the rows of the DataFrame
    for index, row in data.iterrows():
        object = {
            "product_name": row["product_title"],
            "review": row["review"],
            "rating": row["rating"],
            "summary": row["summary"]
        }

        # Append the object to the product list
        product_list.append(object)

    docs = []
    for entry in product_list:
        metadata = {
            "product_name": entry['product_name'],
            "rating": entry['rating'],
            "summary": entry['summary']
        }
        doc = Document(page_content=entry['review'], metadata=metadata)
        docs.append(doc)

    return docs
