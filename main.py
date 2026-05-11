from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ListProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp
from datetime import datetime

import database as db

Window.size = (400, 700)

# ---------------- LOGIN ----------------
class LoginScreen(Screen):
    error_msg = StringProperty('')

    def verify_login(self, u, p):
        if db.verify_user(u.strip(), p.strip()):
            self.manager.current = 'dashboard'
            self.error_msg = ''
        else:
            self.error_msg = 'Invalid username or password'

# ---------------- DASHBOARD ----------------
class Dashboard(Screen):
    total_items_text = StringProperty('0 Items')
    low_stock_text = StringProperty('0 Items')
    sales_today_text = StringProperty('₱0.00')
    profit_today_text = StringProperty('₱0.00')
    low_stock_bg = ListProperty([0.13, 0.14, 0.18, 1])

    def on_enter(self):
        self.load_dashboard_stats()

    def load_dashboard_stats(self):
        products = db.get_products()
        total_items = len(products)
        low_stock = sum(1 for p in products if p[5] is not None and p[5] < 5)

        today = datetime.now().strftime('%Y-%m-%d')
        summary = db.get_sales_summary(today, today)
        total_sales = summary[1] if summary and summary[1] else 0
        total_profit = summary[2] if summary and summary[2] else 0

        self.total_items_text = f"{total_items} Items"
        self.low_stock_text = f"{low_stock} Items"
        self.sales_today_text = f"₱{total_sales:.2f}"
        self.profit_today_text = f"₱{total_profit:.2f}"
        self.low_stock_bg = [0.8, 0.2, 0.2, 1] if low_stock else [0.13, 0.14, 0.18, 1]

    def nav(self, screen_name):
        self.manager.current = screen_name

# ---------------- INVENTORY ----------------
class InventoryScreen(Screen):
    selected_product = None
    all_products = []

    def on_enter(self):
        self.load_products()

    def load_products(self):
        self.all_products = db.get_products()
        self.filter_products('')

    def filter_products(self, query):
        self.ids.inv_list.clear_widgets()
        query = query.lower()

        filtered = [p for p in self.all_products if query in p[1].lower() or query in (p[2] or '').lower()]

        for p in filtered:
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.button import Button
            from kivy.uix.label import Label
            
            pid, pname, cat, cost, retail, stock, expiry, arrival = p
            profit = retail - cost
            
            # Create product card
            card = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), spacing=dp(10))
            
            # Info section
            info_layout = BoxLayout(orientation='vertical', size_hint_x=0.6)
            info_layout.add_widget(Label(text=f"[b]{pname}[/b]", markup=True, size_hint_y=0.3))
            info_layout.add_widget(Label(text=f"Stock: {stock} | ₱{profit:.2f} profit/unit", size_hint_y=0.3, font_size='11sp'))
            info_layout.add_widget(Label(text=f"Exp: {expiry} | Arr: {arrival}", size_hint_y=0.3, font_size='10sp'))
            card.add_widget(info_layout)
            
            # Buttons section
            btn_layout = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=dp(5))
            edit_btn = Button(text='Edit', size_hint_y=0.5)
            edit_btn.product_id = pid
            edit_btn.bind(on_release=self.edit_product)
            
            delete_btn = Button(text='Delete', size_hint_y=0.5)
            delete_btn.product_id = pid
            delete_btn.bind(on_release=self.delete_product)
            
            btn_layout.add_widget(edit_btn)
            btn_layout.add_widget(delete_btn)
            card.add_widget(btn_layout)
            
            self.ids.inv_list.add_widget(card)

    def edit_product(self, instance):
        product_id = instance.product_id
        product = db.get_product_by_id(product_id)
        if product:
            edit_screen = self.manager.get_screen('edit')
            edit_screen.load_product(product)
            self.manager.current = 'edit'

    def delete_product(self, instance):
        product_id = instance.product_id
        db.delete_product(product_id)
        self.load_products()

# ---------------- MANAGE ----------------
class ManageScreen(Screen):
    status_msg = StringProperty('')

    def search_existing(self, query):
        if not query:
            self.status_msg = ''
            return
        products = db.get_products()
        matches = [p[1] for p in products if query.lower() in p[1].lower()]
        if matches:
            self.status_msg = f"Similar: {', '.join(matches[:3])}"
        else:
            self.status_msg = ''

    def save(self, n, cat, c, r, s, e, a):
        try:
            db.add_product(n.strip(), cat.strip(), float(c), float(r), int(s), e.strip(), a.strip())
            self.status_msg = "Product added!"
            # Clear fields
            self.ids.n.text = ''
            self.ids.cat.text = ''
            self.ids.c.text = ''
            self.ids.r.text = ''
            self.ids.s.text = ''
            self.ids.e.text = ''
            self.ids.a.text = ''
        except Exception as ex:
            self.status_msg = f"Invalid input: {str(ex)}"

# ---------------- EDIT ----------------
class EditScreen(Screen):
    status_msg = StringProperty('')
    product_id = None

    def load_product(self, product):
        pid, pname, cat, cost, retail, stock, expiry, arrival = product
        self.product_id = pid
        self.ids.n.text = pname
        self.ids.cat.text = cat if cat else ''
        self.ids.c.text = str(cost)
        self.ids.r.text = str(retail)
        self.ids.s.text = str(stock)
        self.ids.e.text = expiry if expiry else ''

    def save(self, n, cat, c, r, s, e):
        try:
            db.edit_product(self.product_id, n.strip(), cat.strip(), float(c), float(r), int(s), e.strip())
            self.status_msg = "Product updated!"
            self.manager.current = 'inventory'
        except Exception as ex:
            self.status_msg = f"Invalid input: {str(ex)}"

# ---------------- REPORTS ----------------
class ReportScreen(Screen):

    def on_enter(self):
        self.load_report()

    def load_report(self, date_from='', date_to=''):
        self.ids.report_list.clear_widgets()
        
        # Get summary
        summary = db.get_sales_summary(date_from, date_to)
        total_sales, total_revenue, total_profit = summary if summary[0] else (0, 0, 0)
        
        from kivy.uix.label import Label
        
        # Summary section
        self.ids.report_list.add_widget(
            Label(
                text=f"[b]Sales Summary[/b]\nTotal Sales: {int(total_sales) if total_sales else 0}\nTotal Revenue: ₱{total_revenue if total_revenue else 0:.2f}\nTotal Profit: ₱{total_profit if total_profit else 0:.2f}",
                markup=True,
                size_hint_y=None,
                height=dp(100),
                font_size='12sp'
            )
        )
        
        # Sales detail
        self.ids.report_list.add_widget(
            Label(
                text="[b]Recent Sales[/b]",
                markup=True,
                size_hint_y=None,
                height=dp(30),
                font_size='12sp'
            )
        )
        
        sales = db.get_sales_report(date_from, date_to)
        for sale in sales[:20]:  # Show last 20 sales
            pname, qty, revenue, profit, date = sale
            self.ids.report_list.add_widget(
                Label(
                    text=f"{pname}: {qty} units | ₱{revenue:.2f} | Profit: ₱{profit:.2f}\n{date}",
                    size_hint_y=None,
                    height=dp(50),
                    font_size='10sp'
                )
            )

    def filter_report(self, date_from, date_to):
        self.load_report(date_from.strip(), date_to.strip())

# ---------------- SALE ----------------
class SaleScreen(Screen):
    status_msg = StringProperty('')
    products = []

    def on_enter(self):
        self.load_products()
        # Clear search input when entering the screen
        if 'prod_search' in self.ids:
            self.ids.prod_search.text = ''

    def load_products(self):
        self.products = db.get_products()
        self.filter_products('')

    def filter_products(self, query):
        if not self.products:
            self.ids.prod_spinner.values = []
            self.ids.prod_spinner.text = "No products available"
            return
            
        query = query.lower()
        filtered = [p[1] for p in self.products if query in p[1].lower()]
        self.ids.prod_spinner.values = filtered
        if filtered:
            self.ids.prod_spinner.text = filtered[0]
        else:
            self.ids.prod_spinner.text = "No products found"

    def process(self, name, qty):
        try:
            qty = int(qty)
            if qty <= 0:
                raise ValueError
        except:
            self.status_msg = "Invalid quantity"
            return

        product = next((p for p in self.products if p[1] == name), None)

        if not product:
            self.status_msg = "Select a product"
            return

        pid, pname, cat, cost, retail, stock, expiry, arrival = product

        if qty > stock:
            self.status_msg = "Not enough stock"
            return

        tr, tp = db.record_sale(pid, pname, qty, retail)
        self.status_msg = f"Sale done! P{tr:.2f}"
        # Clear inputs after successful sale
        if 'qty' in self.ids:
            self.ids.qty.text = ''
        self.ids.prod_spinner.text = 'Select product' if self.products else 'No products'

# ---------------- SETTINGS ----------------

class SettingsScreen(Screen):
    status_msg = StringProperty('')
    status_color = ListProperty([1, 0.3, 0.3, 1])  # Red for errors

    def update_account(self, current_username, current_password, new_username, new_password, confirm_password):
        # Clear previous message
        self.status_msg = ''

        current_username = current_username.strip() if current_username else ''
        current_password = current_password or ''
        new_username = new_username.strip() if new_username else ''
        new_password = new_password or ''
        confirm_password = confirm_password or ''

        # Validate inputs
        if not all([current_username, current_password, new_username, new_password, confirm_password]):
            self.status_msg = "All fields are required"
            self.status_color = [1, 0.3, 0.3, 1]
            return

        if new_password != confirm_password:
            self.status_msg = "New passwords do not match"
            self.status_color = [1, 0.3, 0.3, 1]
            return

        success, message = db.update_user(current_username, current_password, new_username, new_password)
        self.status_msg = message
        self.status_color = [0.3, 1, 0.3, 1] if success else [1, 0.3, 0.3, 1]

        if success:
            self.clear_inputs()
            # Optional security improvement: force re-login on credential change
            self.manager.current = 'login'

    def reset_data(self):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        
        # Create confirmation popup
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text="Are you sure? This will delete ALL products and sales data."))
        
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        
        def confirm(instance):
            success, message = db.reset_system_data()
            self.status_msg = message
            self.status_color = [0.3, 1, 0.3, 1] if success else [1, 0.3, 0.3, 1]
            popup.dismiss()
        
        def cancel(instance):
            popup.dismiss()
        
        btn_layout.add_widget(Button(text="Cancel", on_release=cancel))
        btn_layout.add_widget(Button(text="Confirm", on_release=confirm, background_color=[1, 0.3, 0.3, 1]))
        
        content.add_widget(btn_layout)
        
        popup = Popup(title="Reset System Data", content=content, size_hint=(0.8, 0.4))
        popup.open()

    def clear_inputs(self):
        if hasattr(self, 'ids'):
            for field in ['current_username', 'current_password', 'new_username', 'new_password', 'confirm_password']:
                if field in self.ids:
                    self.ids[field].text = ''

# ---------------- APP ----------------
class SariSariApp(App):
    def build(self):
        db.init_db()
        return Builder.load_file("inventory.kv")

if __name__ == "__main__":
    SariSariApp().run()