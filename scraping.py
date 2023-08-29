# The app is created with the goal of learning python coding.

# App for scraping top Lithuanian web-stores for gaming computer and their prices by Tomas Suslavicius

# Import necessary libraries
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import textwrap
import webbrowser
from threading import Thread
import time
import queue

from bs4 import BeautifulSoup # BeautifulSoup in app used for simple sites without javascript
import requests
from requests.exceptions import RequestException

from selenium import webdriver # Selenium used for sites empowered with javascript
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

# Set DPI Awareness
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

##################################################################
# Create logotype picture list to show available stores for user #
##################################################################

class Logos(ttk.LabelFrame):
    """Display picture logos of available stores in main window to the left"""
    
    def __init__(self, parent):
        
        # Create label frame for picture logos
        super().__init__(parent)
        self.configure(text="Stores available", labelanchor="n", padding=50)
        self.grid(row=1, column=0, sticky = 'ne')
        
        # Create a list of pictures
        self.list_of_logos = os.listdir('images')
        self.list_count = len(self.list_of_logos)
        self.display_logos()
    
    def display_logos(self):
        """Show picture logos in canvas widget"""
        
        # Create canvas widget
        canvas = tk.Canvas(self, background='gray94', bd=0, highlightthickness=0, relief='flat')
        canvas.config(width=200, height=50 * self.list_count)
        canvas.grid(column=0, row=1, sticky = 'nsew')

        # Insert picture logos into canvas widget
        self.img_ref = [] # To save image references from python garbage collection
        for index, logo in enumerate(self.list_of_logos):
            file_path = f"images/{logo}"
            logo_original = Image.open(file_path)
            resized_logo = logo_original.resize((200, 50), Image.Resampling.LANCZOS)
            logo_image_tk = ImageTk.PhotoImage(resized_logo)
            canvas.create_image(0, 50 * index, image=logo_image_tk, anchor='nw')
            self.img_ref.append(logo_image_tk)

#################################################
# Create search buttons and search entry widget #
#################################################

class Buttons(ttk.LabelFrame):
    """Create search buttons and search entry widget in main window to the right"""

    def __init__(self, parent):
        
        # Create label frame for search buttons and entry widget
        super().__init__(parent)
        self.configure(text="Search stores", labelanchor="n", padding=50)
        self.grid(row=1, column=1, sticky = 'nw')

        # Create checkbutton for search filter of results
        self.checkbutton_var = tk.BooleanVar(value=True)
        checkbutton = ttk.Checkbutton(self, variable=self.checkbutton_var, offvalue=False, onvalue=True, text="Filter search by 1800-2400€", )
        checkbutton.pack(expand = True, fill = 'both', pady = 10)

        # Name buttons and store search strings in a dictionary
        dict_of_buttons = {
                    'HP 32 GB RTX 3070 Ti': 'hp 32 gb rtx 3070 ti',
                    'LENOVO 32 GB RTX 3070 Ti': 'lenovo 32 gb rtx 3070 ti',
                    'HP i7 32 GB RTX 3070 Ti': 'hp i7 32 gb rtx 3070 ti',
                    'LENOVO i7 32 GB RTX 3070 Ti': 'legion i7 32 gb rtx 3070 ti',
                    'DELL 32 GB RTX 3070 Ti': 'dell 32 gb rtx 3070 ti',
                    '32 GB RTX 3070 ti': '32 gb rtx 3070 ti',
                    }
        
        # Create and store buttons in a dictionary for multiple actions (enable/disable)
        self.buttons = []
        for key, value in dict_of_buttons.items():
            self.buttons.append(self.create_buttons(key, value))
        
        # Create entry widget and search button for custom search
        self.entry = ttk.Entry(self)
        self.entry.pack(expand = True, fill = 'both', pady = 0)
        custom_search_button = ttk.Button(self, text="↑↑↑ Custom search ↑↑↑", command=self.custom_search)
        custom_search_button.pack(expand = True, fill = 'both', pady = 0)
        self.buttons.append(custom_search_button)

    def create_buttons(self, button_text, search_string):
        """Create multiple search buttons from a list"""
        
        button = ttk.Button(self, text=button_text, command=lambda: self.button_pressed(search_string))
        button.pack(expand = True, fill = 'both', pady = 10)
        return button

    def button_pressed(self, search_string):
        """Command for button when pressed - start scraping"""
        
        self.disable_all_buttons()
        self.master.request_and_result(search_string)

    def disable_all_buttons(self):
        """Disable all buttons during scraping"""
        
        for button in self.buttons:
            button.config(state='disabled')

    def enable_all_buttons(self):
        """Enable all buttons after the scraping finished"""
        
        for button in self.buttons:
            button.config(state='normal')

    def custom_search(self):
        """Get search string from the entry widget - start scraping"""
        
        self.entry_text = self.entry.get()
        if len(self.entry_text) < 5:
            pass
        else:
            self.disable_all_buttons()
            self.master.request_and_result(self.entry_text)

##############################
# Building log messages area #
##############################

class LogArea(ttk.LabelFrame):
    """Creates textbox widget in the bottom of main window to show log messages"""

    def __init__(self, parent, *args, **kwargs):
        
        # Create label frame for text widget with scrollbar
        super().__init__(parent, *args, **kwargs)
        self.configure(text="Log messages", labelanchor="n", padding=10)
        self.grid(row=2, column=0, columnspan=2)
        
        # Create scrollbar and text widget
        scroll_bar_log = ttk.Scrollbar(self, orient='vertical')
        scroll_bar_log.pack(side='right', fill='y')
        self.log_area = tk.Text(self, padx=10, pady=10, width=65, height=10, background='gray94', yscrollcommand=scroll_bar_log.set)
        scroll_bar_log.config(command=self.log_area.yview)
        self.log_area.pack(expand=True, fill='both')
        self.insert_log_message("App launched successfully. Press any search button or enter string in search box (not less then FIVE characters)...")

    def insert_log_message(self, message):
        """Insert log messages in log area"""

        self.message = message
        lines = textwrap.wrap(self.message, 64)
        self.log_area.config(state='normal')
        for line in lines:
            self.log_area.insert('end', f"{line}\n")
        self.log_area.config(state='disabled')
        self.log_area.see('end')

###################################
# Creating a Result window widget #
###################################

class ShowResults(tk.Toplevel):
    """Opens new window with search results displayed as a list"""

    def __init__(self, app_class_instance, log_area_class_instance, *args, **kwargs):
        
        # Set title and geometry of new window
        super().__init__( *args, **kwargs)
        self.title("Search Results")
        self.geometry(f'700x838+{window_x}+{window_y}') # Window position is set in App class
        
        # Store references to instances of App and LogArea classes 
        self.app = app_class_instance
        self.log_area = log_area_class_instance

        # Create text box widget with scrollbar to show search results
        scroll_bar = ttk.Scrollbar(self, orient='vertical')
        scroll_bar.pack(side='right', fill='y')
        self.result_area = tk.Text(self, padx=10, pady=10, height=47, background='gray94', yscrollcommand=scroll_bar.set)
        scroll_bar.config(command=self.result_area.yview)
        self.result_area.pack(expand=True, fill='both')

        # Create 'close window' button at the bottom of window
        button_close = ttk.Button(self, text="Close window", command=self.destroy)
        button_close.pack()

        # Configure text formatting tags for formatting text in 'result window'
        self.result_area.tag_configure("bold", font=("TkDefaultFont", 12, "bold"))
        self.result_area.tag_configure("boldred", font=("TkDefaultFont", 12, "bold"), foreground="red")
        self.result_area.tag_configure("boldgrey", font=("TkDefaultFont", 12, "bold"), foreground="grey")
        self.result_area.tag_configure("red", foreground="red")
        self.result_area.tag_configure("link", foreground="blue", underline=True)


    def bind_link(self, url):
        """Bind function 'open_link' with tag of the web link part of the text"""

        return lambda e: self.app.open_link(url)

    def enter_link(self, event):
        """Change mouse cursor to 'hand' when over the link"""

        self.result_area.config(cursor="hand2")

    def leave_link(self, event):
        """Change mouse cursor to default when over the link"""

        self.result_area.config(cursor="") 

    def insert_results(self, product_list, search_string):
        """Insert search results in the result window"""

        # Allow to insert text
        self.result_area.config(state='normal')

        # Insert label for what was searched
        self.search_string = search_string
        self.result_area.insert('end', f"                                        SEARCH RESULTS FOR: {self.search_string}\n\n", "boldgrey")

        # Show info message if no rezults found
        if len(product_list) == 0:
            self.result_area.insert('end', f"                                        NO RESULTS IN PRICE RANGE 1800-2400€", "boldred")

        # Show product list in result window    
        for item in product_list:
            self.result_area.insert('end', f"{item['Description']}\n", "bold")
            self.result_area.insert('end', f"          {item['Price']}\n", "boldred")
            tag = f"link-{item['Link']}"
            self.result_area.insert('end', f"{item['Link']}\n\n", (tag, "link"))
            self.result_area.tag_bind(tag, '<Button>', self.bind_link(item['Link']))
            self.result_area.tag_bind(tag, '<Enter>', self.enter_link)
            self.result_area.tag_bind(tag, '<Leave>', self.leave_link)
        
        # Restrict editing in result window
        self.result_area.config(state='disabled')

        # Show log message
        self.log_area.insert_log_message("Results are presented in separate window 'Search Results'")

#####################################
# Scraping web pages of nine stores #
#####################################

class GetItems():
    """Getting web page scraping results - product list"""

    def __init__(self, app_class_instance, log_area_class_instance):
        
        # Inherit from other classes
        self.app = app_class_instance
        self.log_area = log_area_class_instance

    def quantity_items_to_log(self, quantity):
        """Function to send messages to log area"""

        self.app.queue.put(f"                    Items found: {quantity}")

    def get_product_list(self, search_string, filter_status):
        """Function for managing requests and get final product list"""


######## Manage requests and get product lists ########

        # Store: HP store
        self.app.queue.put("Scraping HP store...")
        adapted_search_string = search_string.replace(" ", "+")
        url_hpstore = f"https://www.hpstore.lt/index.php?stoken=E6364813&force_sid=&lang=2&cl=search&searchparam={adapted_search_string}&button="
        self.doc_hpstore = self.get_pages(url_hpstore)
        self.items_hpstore = self.get_items_hpstore(self.doc_hpstore)
        self.quantity_items_to_log(len(self.items_hpstore))

        # Store: Nesiojami
        self.app.queue.put("Scraping Nesiojami...")
        adapted_search_string = search_string.replace(" ", "+")
        url_nesiojami = f"https://nesiojami.lt/nesiojami-kompiuteriai-asus-acer-msi-lenovo-gigabyte/?orderby=price&s={adapted_search_string}"
        self.doc_nesiojami = self.get_pages(url_nesiojami)
        self.items_nesiojami = self.get_items_nesiojami(self.doc_nesiojami)
        self.quantity_items_to_log(len(self.items_nesiojami))

        # Store: Kilobaitas
        self.app.queue.put("Scraping Kilobaitas...")
        adapted_search_string = search_string.replace(" ", "%20")
        url_kilobaitas = f"https://www.kilobaitas.lt/paieskos_rezultatai/searchresult.aspx?groupfilterid=34&q={adapted_search_string}"
        self.doc_kilobaitas = self.get_pages(url_kilobaitas)
        self.items_kilobaitas = self.get_items_kilobaitas(self.doc_kilobaitas)
        self.quantity_items_to_log(len(self.items_kilobaitas))

        # Store: Skytech
        self.app.queue.put("Scraping Skytech...")
        adapted_search_string = search_string.replace(" ", "+")
        url_skytech = f"https://www.skytech.lt/search.php?keywords={adapted_search_string}&x=14&y=14&search_in_description=0&pagesize=100&f=86_165"
        self.doc_skytech = self.get_pages(url_skytech)
        self.items_skytech = self.get_items_skytech(self.doc_skytech)
        self.quantity_items_to_log(len(self.items_skytech))

        # Store: Senukai
        self.app.queue.put("Scraping Senukai. Hidden browser will open and close. Please wait...")
        adapted_search_string = search_string.replace(" ", "+")
        url_senukai = f"https://www.senukai.lt/paieska/?c3=Kompiuterin%C4%97+technika%2C+biuro+prek%C4%97s%2F%2FNe%C5%A1iojami+kompiuteriai+ir+priedai%2F%2FNe%C5%A1iojami+kompiuteriai&q={adapted_search_string}"
        self.script_senukai = ".ks-product-grid-row"
        self.doc_senukai = self.get_pages_java_script(url_senukai, self.script_senukai)
        if not self.doc_senukai:
            self.items_senukai = []
        else:
            self.items_senukai = self.get_items_senukai(self.doc_senukai)
        self.driver.quit() # Closes Chrome browser opened by Selenium webdriver
        self.quantity_items_to_log(len(self.items_senukai))

        # Store: 1a.lt
        self.app.queue.put("Scraping 1a. Hidden browser will open and close. Please wait...")
        url_1a = "https://www.1a.lt/c/kompiuterine-technika-biuro-prekes/nesiojami-kompiuteriai-ir-priedai/nesiojami-kompiuteriai/371?f=u1Z3yjZbjam"
        self.script_1a = ".catalog-taxons-products-container__grid-row"
        self.doc_1a = self.get_pages_java_script(url_1a, self.script_1a)
        if not self.doc_1a:
            self.items_1a = []
        else:
            self.items_1a = self.get_items_1a(self.doc_1a)
        self.driver.quit() # Closes Chrome browser opened by Selenium webdriver
        self.quantity_items_to_log(len(self.items_1a))

        # Store: Varle
        self.app.queue.put("Scraping Varle. Hidden browser will open and close. Please wait...")
        adapted_search_string = search_string.replace(" ", "%20")
        url_varle = f"https://www.varle.lt/nesiojami-kompiuteriai/nesiojami-kompiuteriai/?cq={adapted_search_string}&f.s-gamintojas=HP&f.s-gamintojas=Lenovo&f.s-gamintojas=Dell"
        self.script_varle = ".grid.three-in-row"
        self.doc_varle = self.get_pages_java_script(url_varle, self.script_varle)
        if not self.doc_varle:
            self.items_varle = []
        else:
            self.items_varle = self.get_items_varle(self.doc_varle)
        self.driver.quit() # Closes Chrome browser opened by Selenium webdriver
        self.quantity_items_to_log(len(self.items_varle))

        # Store: RDE.lt
        self.app.queue.put("Scraping RDE. Hidden browser will open and close. Please wait...")
        url_rde = "https://www.rde.lt/categories/lt/150/sort/5/filter/0_0_219.142.191_1006757.1007229.1007307/page/1/Ne%C5%A1iojami-kompiuteriai.html"
        self.script_rde = ".product-list"
        self.doc_rde = self.get_pages_java_script(url_rde, self.script_rde, find_multiple=True)
        if not self.doc_rde:
            self.items_rde = []
        else:
            self.items_rde = self.get_items_rde(self.doc_rde)
        self.driver.quit() # Closes Chrome browser opened by Selenium webdriver
        self.quantity_items_to_log(len(self.items_rde))

        # Store: Pigu
        self.app.queue.put("Scraping Pigu. Hidden browser will open and close. Please wait...")
        adapted_search_string = search_string.replace(" ", "%20")
        url_pigu = f"https://pigu.lt/lt/search?q={adapted_search_string}&c[50]=50&filter[attr_UHJla8SXcyDFvmVua2xhcw][2]=RGVsbA&filter[attr_UHJla8SXcyDFvmVua2xhcw][4]=TGVub3Zv&filter[attr_UHJla8SXcyDFvmVua2xhcw][5]=SFA"
        self.script_pigu = ".product-list.all-products-visible"
        self.doc_pigu = self.get_pages_java_script(url_pigu, self.script_pigu, find_multiple=False)
        if not self.doc_pigu:
            self.items_pigu = []
        else:
            self.items_pigu = self.get_items_pigu(self.doc_pigu)
        self.driver.quit() # Closes Chrome browser opened by Selenium webdriver
        self.quantity_items_to_log(len(self.items_pigu))


######## Consolidate and filter product list ########

        self.app.queue.put("Scraping finished. Creating list of products found...")

        # Create the list of all products found
        self.product_list_total_interim = self.items_hpstore + self.items_nesiojami + self.items_kilobaitas + self.items_skytech + self.items_senukai + self.items_1a + self.items_varle + self.items_rde + self.items_pigu
        self.app.queue.put(f"Total items found: {len(self.product_list_total_interim)}")
        
        # Filter search result by brand name
        if len(self.product_list_total_interim) >= 1:
            brand_names_all = ["hp", "lenovo", "dell", "acer", "asus", "gigabyte", "msi", "razer"]
            for brand_name in brand_names_all:
                if brand_name in search_string.lower():
                    search_string_total = brand_name
                    break
                else:
                    search_string_total = ""
            self.product_list_total = [item for item in self.product_list_total_interim if search_string_total in item["Description"].lower()]          
            self.app.queue.put(f"Items after brand filter: {len(self.product_list_total)}")
            
            # Filtering second time for some known mistakes
            filter_string_all = ["rtx3050", "rtx3060", "16gb", "512 gb", "512ssd", "dos"]
            for filter_string in filter_string_all:
                self.product_list_total = [item for item in self.product_list_total if filter_string not in item["Description"].lower()]
            self.app.queue.put(f"Items after known mistakes filter: {len(self.product_list_total)}")
        else:
            self.product_list_total = self.product_list_total_interim
        
        # Sorting the list by price
        self.sorted_list_by_price = sorted(self.product_list_total, key=lambda i: i['Price'])
        
        # Apply price filter 1800-2400 euros
        if filter_status:
            filtered_list = []
            for i in range(len(self.sorted_list_by_price)):
                if not (self.sorted_list_by_price[i]["Price"] < 1800 or self.sorted_list_by_price[i]["Price"] > 2400):
                    filtered_list.append(self.sorted_list_by_price[i])
            self.sorted_list_by_price = filtered_list
            self.app.queue.put(f"Items after price filter: {len(self.sorted_list_by_price)}\n\n")
        return self.sorted_list_by_price

######## Get pages content using BeautifulSoup and Selenium ########

    def get_pages(self, url):
        """Getting page content with Beautiful Soup"""

        self.url = url
        try:
            self.response = requests.get(self.url, timeout=5, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0"})
            self.response.raise_for_status()
            self.page = self.response.content
        except RequestException as e:
            self.app.queue.put(f"Failed to get webpage: {e}")
            return None
        else:
            self.doc = BeautifulSoup(self.page, "html.parser")
            return self.doc

    def get_pages_java_script(self, url, script, find_multiple=False):
        """Getting page content with Selenium for pages with javascript"""

        self.url = url
        self.script = script
        self.options = Options()
        self.options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(3)
        try:
            self.driver.get(self.url)
            if find_multiple: # For pages that return multiple tables with search results
                self.doc = self.driver.find_elements(By.CSS_SELECTOR, self.script)
                if not self.doc:
                    self.app.queue.put(f"No elements found with the provided CSS selector on: {self.url[:20]}")
                    return None
            else:
                self.doc = self.driver.find_element(By.CSS_SELECTOR, self.script)
        except NoSuchElementException:
            self.app.queue.put(f"No elements found with the provided CSS selector on: {self.url[:45]}...")
            return None
        except Exception as e:
            self.app.queue.put(f"An error occurred: {str(e)}")
            return None
        return self.doc

######## Get products from the webpage content for each of 9 stores ########

    def get_items_hpstore(self, doc):

        self.doc = doc
        self.table = self.doc.find(class_="infogrid products")
        #print(self.table.prettify()) # Left in case revision is required
        if self.table == None:
            self.product_list = [{'Description': 'HP Store: The products you were looking for were not found in the store', 'Price': 0, 'Link': "Search manually: https://www.hpstore.lt/"}]
            return self.product_list
        self.items = self.table.find_all('li')
        self.product_list = []
        self.product = {}
        for self.item in self.items:
            self.product["Description"] = self.item.find('a').get('title')
            self.product["Link"] = self.item.find('a').get('href')
            self.product["Price"] = float(self.item.find('big2').get_text().split(" ")[0].replace(",", "."))
            self.product_list.append(self.product.copy())
        return self.product_list

    def get_items_nesiojami(self, doc):

        self.doc = doc
        self.table = self.doc.find(class_="products columns-4")
        #print(self.table.prettify()) # Left in case revision is required
        if self.table == None:
            self.product_list = [{'Description': 'Nesiojami: The products you were looking for were not found in the store', 'Price': 0, 'Link': "Search manually: https://nesiojami.lt/"}]
            return self.product_list
        self.items = self.table.find_all('li')
        self.product_list = []
        self.product = {}
        for self.item in self.items:
            self.product["Description"] = self.item.find('h2', attrs={"class": "woocommerce-loop-product__title"}).get_text()
            self.product["Link"] = self.item.find('a').get('href')
            self.product["Price"] = float(self.item.find('bdi').get_text().replace(",", "").replace(" €", ""))
            self.product_list.append(self.product.copy())
        return self.product_list

    def get_items_kilobaitas(self, doc):

        self.doc = doc
        self.table = self.doc.find(class_="products-grid row")
        #print(self.table.prettify()) # Left in case revision is required
        if self.table == None:
            self.product_list = [{'Description': 'Kilobaitas: The products you were looking for were not found in the store', 'Price': 0, 'Link': "Search manually: https://www.kilobaitas.lt/"}]
            return self.product_list
        self.items = self.table.find_all('div', class_='item-inner')
        self.product_list = []
        self.product = {}
        for self.item in self.items:
            self.product["Description"] = self.item.find('div', class_="item-title line-clamp").find('p').get_text()
            self.product["Link"] = "https://www.kilobaitas.lt" + self.item.find('div', class_="item-title line-clamp").find('a').get('href')
            self.product["Price"] = float(self.item.find('div', class_="item-price").find_all('meta')[1].get('content'))
            self.product_list.append(self.product.copy())
        return self.product_list

    def get_items_skytech(self, doc):

        self.doc = doc
        self.table = self.doc.find('table', class_="productListing")
        #print(self.table.prettify()) # Left in case revision is required
        check_string = "prekių, atitinkančių"
        if check_string in str(self.table):
            self.product_list = [{'Description': 'Skytech: The products you were looking for were not found in the store', 'Price': 0, 'Link': "Search manually: https://www.skytech.lt/"}]
            return self.product_list
        self.items = self.table.find_all(class_=["productListing odd", "productListing even"])
        self.product_list = []
        self.product = {}
        for self.item in self.items:
            self.product["Description"] = self.item.find('td', class_="name").find('a').get_text().strip()
            self.product["Link"] = "https://www.skytech.lt/" + self.item.find('td', class_="name").find('a').get('href')
            self.product["Price"] = float(self.item.find('td', class_="name").find_next_siblings('td')[1].find('strong').get_text().replace(" ", "").replace("€", ""))
            self.product_list.append(self.product.copy())
        return self.product_list

    def get_items_senukai(self, doc):

        self.doc = doc
        self.items = self.doc.find_elements(By.CLASS_NAME, "sn-product-inner.sn-product-inner--hover.ks-gtm-categories")
        self.product_list = []
        if len(self.items) < 1:
            self.product_list = [{'Description': 'Senukai Store: The products you were looking for were not found in the store', 'Price': 0, 'Link': "Search manually: https://www.senukai.lt/"}]
            return self.product_list
        self.product = {}
        for self.item in self.items:
            self.product['Description'] = self.item.find_element(By.CLASS_NAME, "ks-new-product-name").get_attribute("innerHTML")
            self.product['Link'] = self.item.find_element(By.CLASS_NAME, "ks-new-product-name").get_attribute('href')
            self.product_price_item_interim = self.item.find_element(By.CLASS_NAME, "ks-item-price ")
            self.product['Price'] = float(self.product_price_item_interim.find_element(By.TAG_NAME, 'span').get_attribute("innerHTML").replace("&nbsp;", "").replace(",", ".").replace("€", "").replace(" ", ""))
            try:
                self.product['Price'] = float(self.item.find_element(By.CLASS_NAME, "ks-new-product-price__price-number").get_attribute("innerHTML").replace("&nbsp;", "").replace(",", ".").replace("€", "").replace(" ", ""))
            except NoSuchElementException:
                pass
            self.product_list.append(self.product.copy())
        return self.product_list
        
    def get_items_1a(self, doc):

        self.doc = doc
        self.items = self.doc.find_elements(By.CLASS_NAME, "catalog-taxons-product__hover")
        self.product_list = []
        if len(self.items) < 1:
            self.product_list = [{'Description': '1a Store: The products you were looking for were not found in the store', 'Price': 0, 'Link': "Search manually: https://www.1a.lt/"}]
            return self.product_list
        self.product = {}
        for self.item in self.items:
            self.product['Description'] = self.item.find_element(By.CLASS_NAME, "catalog-taxons-product__name").get_attribute("innerHTML").strip()
            self.product['Link'] = self.item.find_element(By.CLASS_NAME, "catalog-taxons-product__name").get_attribute('href')
            self.product_price_item_interim = self.item.find_element(By.CLASS_NAME, "catalog-taxons-product-price__item-price")
            self.product['Price'] = float(self.product_price_item_interim.find_element(By.TAG_NAME, 'span').get_attribute("innerHTML").replace(",", ".").replace(" ", ""))
            self.product_list.append(self.product.copy())
        return self.product_list

    def get_items_varle(self, doc):

        self.doc = doc
        self.items = self.doc.find_elements(By.CSS_SELECTOR, ".GRID_ITEM")
        self.product_list = []
        if len(self.items) < 1:
            self.product_list = [{'Description': 'Varle Store: The products you were looking for were not found in the store', 'Price': 0, 'Link': "Search manually: https://www.varle.lt/"}]
            return self.product_list
        self.product = {}
        for self.item in self.items:
            self.product['Description'] = self.item.find_element(By.CSS_SELECTOR, ".product-title").text.strip().replace("| ", "")
            self.product_link_interim = self.item.find_element(By.CSS_SELECTOR, ".product-title")
            self.product['Link'] = self.product_link_interim.find_element(By.TAG_NAME, "a").get_attribute('href')
            self.product_price_item_interim = self.item.find_element(By.CSS_SELECTOR, ".price-value")
            self.product['Price'] = float(self.product_price_item_interim.find_element(By.TAG_NAME, 'span').text.strip()) + 0.99
            self.product_list.append(self.product.copy())
        return self.product_list

    def get_items_rde(self, doc):

        self.doc_interim = doc
        items_list = []
        for table in self.doc:
            items = table.find_elements(By.CLASS_NAME, "product__info")
            items_list.extend(items)
        self.product_list = []
        if len(items_list) < 1:
            self.product_list = [{'Description': 'RDE Store: The products you were looking for were not found in the store', 'Price': 0, 'Link': "Search manually: https://www.rde.lt/"}]
            return self.product_list
        self.product = {}
        for self.item in items_list:
            self.product['Description'] = self.item.find_element(By.CLASS_NAME, "product__title ").text.replace("\n", " ").strip()
            product_link_interim = self.item.find_element(By.CLASS_NAME, "product__title ")
            self.product['Link'] = product_link_interim.find_element(By.TAG_NAME, "a").get_attribute('href')
            self.product['Price'] = float(self.item.find_element(By.CLASS_NAME, "price").text.replace("€", "").strip())
            self.product_list.append(self.product.copy())
        return self.product_list

    def get_items_pigu(self, doc):

        self.doc = doc
        self.items = self.doc.find_elements(By.CSS_SELECTOR, ".product-item-inner-hover")
        self.product_list = []
        if len(self.items) < 1:
            self.product_list = [{'Description': 'Pigu Store: The products you were looking for were not found in the store', 'Price': 0, 'Link': "Search manually: https://www.pigu.lt/"}]
            return self.product_list
        self.product = {}
        for self.item in self.items:
            self.product['Description'] = self.item.find_element(By.CSS_SELECTOR, "p.product-name > a").get_attribute('title')
            self.product['Link'] = self.item.find_element(By.CSS_SELECTOR, "p.product-name > a").get_attribute('href')
            try:
                self.product['Price'] = float(self.item.find_element(By.CSS_SELECTOR, ".price").text.replace(" ", "").replace("€", "").strip()) / 100
            except NoSuchElementException:
                continue        
            self.product_list.append(self.product.copy())
        return self.product_list

####################################
# Application main window and loop #
####################################

class App(tk.Tk):
    """Initializes main window and runs main loop of the app"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("WEB Scarping App")
        self.geometry("+100+50")
        self.columnconfigure((0, 1), weight=1)
       
        # Insert label in main window to show purpose of the app
        ttk.Label(
          self,
          text="Look for the game computer in the local stores",
          font=("TkDefaultFont", 16),
          padding=10,
        ).grid(row=0, column=0, columnspan=2)

        # Initialize parts of the main window and GetItems class
        self.logos = Logos(self)
        self.search_buttons = Buttons(self)
        self.log_area = LogArea(self)
        self.queue = queue.Queue()
        self.items = GetItems(self, self.log_area)

    def open_link(self, url):
        """Opens default browser with link pressed"""

        webbrowser.get().open(url)

    def check_queue(self):
        """Function to extract messages from queue into terminal"""

        while not self.queue.empty():
            message = self.queue.get_nowait()
            self.log_area.insert_log_message(message)
        self.after(100, self.check_queue)

    def scrape_product_list(self, search_string, filter_status):
        """Main function to operate scraping loop"""

        self.product_list = self.items.get_product_list(search_string, filter_status)
        self.show = ShowResults(self, self.log_area)
        self.show.insert_results(self.product_list, search_string)
        
        # Changes the position of new 'Search results' window every time the function is called
        global window_x
        global window_y
        if window_x < 1200:
            window_x += 50
        else:
            window_x -= 700
        if window_y < 360:
            window_y += 70
        else:
            window_x -= 180
            window_y -= 180

    def request_and_result(self, search_string):
        """Function to start scraping and does it in separate Thread to keep main loop alive and be able show log messages"""
        
        self.log_area.insert_log_message("Search started. Please wait...")
        self.log_area.update_idletasks()
        filter_status = self.search_buttons.checkbutton_var.get()
        self.scrape_thread = Thread(target=self.scrape_product_list, args=(search_string, filter_status))
        self.scrape_thread.start()
        self.after(100, self.check_scrape_thread)
        self.check_queue()

    def check_scrape_thread(self):
        """Function to check Thread progress"""
        if self.scrape_thread.is_alive():
            # If the thread is still running, keep checking every 100ms.
            self.after(100, self.check_scrape_thread)
        else:
            # If the thread has finished, enable the buttons and stop checking.
            self.search_buttons.enable_all_buttons()

# Setting the global values for "Search results" window position
window_x = 700
window_y = 50

if __name__ == "__main__":
    app = App()
    app.mainloop()
