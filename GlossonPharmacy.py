import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import Error
from datetime import datetime
from typing import List, Dict, Tuple


class DatabaseManager:
    def __init__(self, dbname:str, user:str, password:str, host:str, port:str):
        self.dbname=dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = self.connect_to_db()
        
    def connect_to_db(self):
        try:
            conn = psycopg2.connect(
                dbname = self.dbname,
                user = self.user,
                password = self.password,
                host = self.host,
                port = self.port                
            )
            return conn

        except Error as e:
            st.error(f"Error connecting to PostgreSQL database: {e}")
            return None

            
    def execute_query(self, query:str, params: tuple=None):
        try:
            with self.conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Commit the transaction for non-SELECT queries
                if not query.startswith("SELECT"):
                    self.conn.commit()
                    
                # Return fetched data for SELECT queries
                if query.strip().upper().startswith("SELECT"):
                    return cursor.fetchall()             
            
        except Error as e:
            st.error(f"Error executing query: {e}")
            
class InventoryManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def add_item_to_inventory(self, item:str, quantity:int, price:float):
        query = "INSERT INTO inventory (item, quantity, price) VALUES (%s, %s, %s)"
        self.db_manager.execute_query(query, (item, quantity, price))
        
    def get_items_in_inventory(self) -> List[str]:
        query = "SELECT item FROM inventory"
        items = self.db_manager.execute_query(query)
        return [item[0] for item in items] if items else []
    
    def get_items_in_inventory(self) -> List[Tuple[str, int, float]]:
        query = "SELECT item, quantity, price FROM inventory"
        inventory_data = self.db_manager.execute_query(query)
        return inventory_data if inventory_data else []
    
    def get_items_in_sales(self) -> List[Tuple[str,int,float]]:
        '''
        Get items from the sales table sold given the date. Note, 
        default date will be datetime.now()
        '''
        pass
    

class SalesManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def make_sale(self, items_quantities: Dict[str,str], customer:str):
        total_price = 0
        sale_date = datetime.now()
        queries = []
        
        for item, quantity in items_quantities.items():
            item_price = self.get_item_price(item)
            if item_price is None:
                st.error(f"No price found for item: {item}")
                return
            current_quantity = self.get_current_quantity(item)
            if current_quantity < quantity:
                st.error(f"Insufficient quantity for item: {item} in inventory. Avaliable: {current_quantity}")
                return
            sale_price = item_price * quantity
            queries.append(("INSERT INTO sales (item, quantity, price, customer, sale_date) VALUES (%s,%s,%s,%s,%s)",
                           (item, quantity, sale_price, customer, sale_date)))
            queries.append(("UPDATE inventory SET quantity = quantity - %s WHERE item = %s",(quantity,item)))
            total_price += sale_price
            
        for query, params in queries:
            self.db_manager.execute_query(query, params)
        st.success(f"Sale recorded successfully. Total Price: N{total_price:,.2f}")
        
    def get_item_price(self, item:str) -> float:
        query = "SELECT price FROM inventory WHERE item = %s"
        price = self.db_manager.execute_query(query, (item,))
        return price[0][0] if price else None
    
    def get_current_quantity(self, item:str) -> int:
        query = "SELECT quantity FROM inventory WHERE item = %s"
        quantity = self.db_manager.execute_query(query, (item,))
        return quantity[0][0] if quantity else 0
        


def main():
    st.title("Pharmacy Management System")                

    db_manager = DatabaseManager("GlossonDB", "postgres", "feyo", "localhost", "5432")
    inventory_manager = InventoryManager(db_manager)
    sales_manager = SalesManager(db_manager)

    # Sidebar Menu
    menu = ["Home", "Inventory Management", "Sales Tracking"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Home")
        st.write("Welcome to the Pharmacy Management System.")

    elif choice == "Inventory Management":
        st.subheader("Inventory Management")
        st.write("Add new items to the inventory:")
        item = st.text_input("Item")
        quantity = st.number_input("Quantity", value=1, min_value=1)
        price = st.number_input("Price", value=0.0, step=0.01)
        if st.button("Add to Inventory"):
            inventory_manager.add_item_to_inventory(item, quantity, price)

        # st.write("Current Inventory:")
        items_in_inventory = inventory_manager.get_items_in_inventory()    
        selected_item = st.selectbox("Item", items_in_inventory)

        if st.button("View Inventory"):
            st.write("Inventory Details:")
            inventory_data = inventory_manager.get_items_in_inventory()

            if inventory_data:
                column_names = ["Item", "Quantity", "Price"]
                # st.table(inventory_data, header=column_names)
                df_inventory = pd.DataFrame(inventory_data, columns=column_names)
                st.dataframe(df_inventory)

            else:
                st.write("No items in inventory.")

    elif choice == "Sales Tracking":
        st.subheader("Sales Tracking")
        st.write("Record sales transactions:")
        items_in_inventory = inventory_manager.get_items_in_inventory()
        items_list = [item[0] for item in items_in_inventory]
        selected_item = st.selectbox("Select Item to Sell", items_list)
        quantity = st.number_input("Quantity", value=1, min_value=1)
        customer = st.text_input("Customer")
        if st.button("Record Sale"):
            items_quantities = {selected_item: quantity}
            sales_manager.make_sale(items_quantities, customer)

if __name__ == "__main__":
    main()
    
            
        
        
               
        
        
        
        
        
        
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
        
        