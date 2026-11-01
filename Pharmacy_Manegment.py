
import json
import os
import sys
import html
import webbrowser
from pathlib import Path
from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_NAME = "Al-Shifa Pharmacy"
LOW_STOCK_LIMIT = 10

# EXE banne ke baad bhi JSON files EXE ke folder mein hi rahengi.
if getattr(sys, "frozen", False):
    DATA_DIR = Path(sys.executable).resolve().parent
else:
    DATA_DIR = Path(__file__).resolve().parent

MEDICINES_FILE = DATA_DIR / "medicines.json"
SALES_FILE = DATA_DIR / "sales.json"
PHARMACY_SETTINGS_FILE = DATA_DIR / "pharmacy_settings.json"

def load_json(path, default):
    try:
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, type(default)) else default
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path, data):
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    temp_path.replace(path)


def expiry_status(medicine):
    value = medicine.get("expiry", "")
    try:
        expiry = datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return "Date check karein"
    if expiry < date.today():
        return "EXPIRED"
    if expiry <= date.today() + timedelta(days=30):
        return "Expiry qareeb"
    return "Theek"


class PharmacyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1200x760")
        self.root.minsize(980, 650)
        self.root.configure(bg="#F3F6FA")

        self.medicines = load_json(MEDICINES_FILE, [])
        self.sales = load_json(SALES_FILE, [])
        self.settings = load_json(PHARMACY_SETTINGS_FILE, {
    "name": "Al-Shifa Pharmacy",
    "address": "",
    "phone": "",
    "logo": ""
})
        self.root.title(self.settings.get("name", APP_NAME))
        self.current_page = None

        self.setup_style()
        self.build_shell()
        self.show_dashboard()

    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=31,
                        background="white", fieldbackground="white", foreground="#1F2937")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background="#E8EEF5", foreground="#243247", padding=8)
        style.map("Treeview", background=[("selected", "#DCEAFE")],
                  foreground=[("selected", "#14233B")])
        style.configure("TCombobox", padding=7)
        style.configure("TEntry", padding=8)

    def build_shell(self):
        header = tk.Frame(self.root, bg="#10243A", height=76)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=self.settings.get("name", APP_NAME).upper(), bg="#10243A", fg="white",
                 font=("Segoe UI", 20, "bold")).pack(side="left", padx=25)
        tk.Label(header, text="Pharmacy Management System", bg="#10243A", fg="#B8C7D9",
                 font=("Segoe UI", 10)).pack(side="left", padx=8, pady=(14, 0))
        self.clock_label = tk.Label(header, text="", bg="#10243A", fg="#DCE6F1",
                                    font=("Segoe UI", 10))
        self.clock_label.pack(side="right", padx=24)
        self.update_clock()

        body = tk.Frame(self.root, bg="#F3F6FA")
        body.pack(fill="both", expand=True)
        sidebar = tk.Frame(body, bg="#172F49", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        nav_items = [
            ("Dashboard", self.show_dashboard),
            ("Medicine Inventory", self.show_inventory),
            ("Add Medicine", self.show_add_medicine),
            ("Sell Medicine", self.show_sell),
            ("Stock In", self.show_stock_in),
            ("Low Stock Alert", self.show_low_stock),
            ("Expiry Report", self.show_expiry),
            ("Sales History", self.show_sales),
            ("Inventory Report", self.show_report),
            ("Pharmacy Settings", self.show_settings),
        ]
        tk.Label(sidebar, text="MAIN MENU", bg="#172F49", fg="#8FA7C0",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(25, 12))
        for label, command in nav_items:
            btn = tk.Button(sidebar, text=label, command=command, anchor="w",
                            bg="#172F49", fg="white", activebackground="#244766",
                            activeforeground="white", relief="flat", bd=0,
                            font=("Segoe UI", 10), padx=20, pady=12, cursor="hand2")
            btn.pack(fill="x", padx=8, pady=2)
        tk.Frame(sidebar, bg="#36516D", height=1).pack(fill="x", padx=18, pady=18)
        tk.Button(sidebar, text="Exit Application", command=self.exit_app,
                  anchor="w", bg="#172F49", fg="#FFB7B7", activebackground="#244766",
                  activeforeground="white", relief="flat", font=("Segoe UI", 10),
                  padx=20, pady=12, cursor="hand2").pack(fill="x", padx=8)

        self.content = tk.Frame(body, bg="#F3F6FA")
        self.content.pack(side="left", fill="both", expand=True, padx=24, pady=22)

    def update_clock(self):
        self.clock_label.config(text=datetime.now().strftime("%d %b %Y   %I:%M:%S %p"))
        self.root.after(1000, self.update_clock)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def page_title(self, title, subtitle=""):
        top = tk.Frame(self.content, bg="#F3F6FA")
        top.pack(fill="x", pady=(0, 18))
        tk.Label(top, text=title, bg="#F3F6FA", fg="#172B43",
                 font=("Segoe UI", 21, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(top, text=subtitle, bg="#F3F6FA", fg="#718096",
                     font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

    def card(self, parent, title, value, color):
        box = tk.Frame(parent, bg="white", highlightbackground="#E2E8F0",
                       highlightthickness=1, padx=18, pady=16)
        tk.Label(box, text=title, bg="white", fg="#718096",
                 font=("Segoe UI", 10, "bold")).pack(anchor="center")
        tk.Label(box, text=str(value), bg="white", fg=color,
                 font=("Segoe UI", 23, "bold")).pack(anchor="center", pady=(9, 0))
        return box

    def make_table(self, parent, columns, headings=None, height=12):
        wrap = tk.Frame(parent, bg="white")
        wrap.pack(fill="both", expand=True)
        tree = ttk.Treeview(wrap, columns=columns, show="headings", height=height)
        for col in columns:
            tree.heading(col, text=(headings or {}).get(col, col.replace("_", " ").title()), anchor="center")
            tree.column(col, width=125, anchor="center")
        ybar = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        return tree

    def refresh_inventory_table(self, tree, records=None):
        for item in tree.get_children():
            tree.delete(item)
        for med in (self.medicines if records is None else records):
            tree.insert("", "end", values=(
                med.get("name", ""), f'{med.get("price", 0):.2f}',
                med.get("quantity", 0), med.get("expiry", ""),
                expiry_status(med)
            ))

    def show_settings(self):
        self.clear_content()
        self.page_title("Pharmacy Settings", "Update your pharmacy details.")

        form = tk.Frame(self.content, bg="white", padx=25, pady=25)
        form.pack(fill="x", padx=10, pady=10)

        tk.Label(form, text="Pharmacy Name", bg="white").grid(
            row=0, column=0, sticky="w", pady=10
        )
        name_entry = tk.Entry(form, width=40)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.insert(0, self.settings.get("name", ""))

        tk.Label(form, text="Address", bg="white").grid(
            row=1, column=0, sticky="w", pady=10
        )
        address_entry = tk.Entry(form, width=40)
        address_entry.grid(row=1, column=1, padx=10, pady=10)
        address_entry.insert(0, self.settings.get("address", ""))

        tk.Label(form, text="Phone Number", bg="white").grid(
            row=2, column=0, sticky="w", pady=10
        )
        phone_entry = tk.Entry(form, width=40)
        phone_entry.grid(row=2, column=1, padx=10, pady=10)
        phone_entry.insert(0, self.settings.get("phone", ""))

        tk.Label(form, text="Logo", bg="white").grid(
            row=3, column=0, sticky="w", pady=10
        )
        logo_var = tk.StringVar(value=self.settings.get("logo", ""))

        def choose_logo():
            path = filedialog.askopenfilename(
                filetypes=[("PNG and GIF Images", "*.png *.gif")]
            )
            if path:
                logo_var.set(path)

        tk.Button(form, text="Choose Logo", command=choose_logo).grid(
            row=3, column=1, sticky="w", padx=10, pady=10
        )

        def save_settings():
            self.settings = {
                "name": name_entry.get().strip(),
                "address": address_entry.get().strip(),
                "phone": phone_entry.get().strip(),
                "logo": logo_var.get()
            }

            with open(PHARMACY_SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump(self.settings, file, indent=4)

            messagebox.showinfo("Success", "Pharmacy settings saved successfully.")

        tk.Button(
            form,
            text="Save Settings",
            command=save_settings,
            bg="#0F9D78",
            fg="white",
            padx=20,
            pady=8
        ).grid(row=4, column=1, sticky="w", padx=10, pady=20)
        
    def show_dashboard(self):
        self.clear_content()
        pharmacy_name = self.settings.get("name", "ALI_PHARMACY")
        self.page_title("Dashboard", f"Welcome to {pharmacy_name} management.")

        total_units = sum(int(m.get("quantity", 0)) for m in self.medicines)
        low = sum(1 for m in self.medicines if int(m.get("quantity", 0)) <= LOW_STOCK_LIMIT)
        today = date.today().isoformat()
        today_sales = sum(
            float(s.get("total", 0)) for s in self.sales
            if str(s.get("date", "")).startswith(today)
        )
        sales_total = sum(float(s.get("total", 0)) for s in self.sales)

        cards = tk.Frame(self.content, bg="#F3F6FA")
        cards.pack(fill="x")

        for title, value, color in [
            ("Different Medicines", len(self.medicines), "#2563EB"),
            ("Total Units in Stock", total_units, "#0F9D78"),
            ("Low Stock Medicines", low, "#D97706"),
            ("Today's Sales", f"Rs. {today_sales:,.2f}", "#7C3AED"),
        ]:
            self.card(cards, title, value, color).pack(
                side="left", fill="x", expand=True, padx=(0, 12)
            )

        summary = tk.Frame(
            self.content, bg="white", padx=20, pady=18,
            highlightbackground="#E2E8F0", highlightthickness=1
        )
        summary.pack(fill="x", pady=20)

        tk.Label(
            summary, text="Business Snapshot", bg="white", fg="#172B43",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w")

        tk.Label(
            summary, text=f"Recorded sales total: Rs. {sales_total:,.2f}",
            bg="white", fg="#43546A", font=("Segoe UI", 11)
        ).pack(anchor="w", pady=10)

        tk.Label(
            summary, text=f"Data folder: {DATA_DIR}", bg="white",
            fg="#718096", font=("Segoe UI", 9),
            wraplength=850, justify="left"
        ).pack(anchor="w")

        tk.Label(
            self.content, text="Recent Medicines", bg="#F3F6FA",
            fg="#172B43", font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", pady=(0, 8))

        tree = self.make_table(
            self.content,
            ("name", "price", "quantity", "expiry", "status"),
            {
                "name": "Medicine",
                "price": "Sale Price (Rs.)",
                "quantity": "Stock",
                "expiry": "Expiry Date",
                "status": "Status"
            },
            7
        )

        self.refresh_inventory_table(tree)
        
    def show_inventory(self):
        self.clear_content()
        self.page_title("Medicine Inventory", "Search, review, edit or remove medicines.")
        searchrow = tk.Frame(self.content, bg="#F3F6FA")
        searchrow.pack(fill="x", pady=(0, 12))
        query = tk.StringVar()
        entry = ttk.Entry(searchrow, textvariable=query, width=38)
        entry.pack(side="left", ipady=4)
        # Buttons ko table se pehle pack karte hain taake neeche hide na hon.
        actions = tk.Frame(self.content, bg="#F3F6FA")
        actions.pack(side="bottom", fill="x", pady=12)
        tree = self.make_table(self.content, ("name", "price", "quantity", "expiry", "status"),
                               {"name":"Medicine", "price":"Sale Price (Rs.)",
                                "quantity":"Stock", "expiry":"Expiry Date", "status":"Status"})
        def search(*_):
            q = query.get().strip().lower()
            rows = [m for m in self.medicines if q in m.get("name", "").lower()]
            self.refresh_inventory_table(tree, rows)
        query.trace_add("write", search)
        entry.focus_set()
        tk.Button(actions, text="Edit Selected", command=lambda: self.edit_selected(tree),
                  bg="#2563EB", fg="white", relief="flat", padx=16, pady=9).pack(side="left", padx=(0, 8))
        tk.Button(actions, text="Delete Selected", command=lambda: self.delete_selected(tree),
                  bg="#B42318", fg="white", relief="flat", padx=16, pady=9).pack(side="left")
        self.refresh_inventory_table(tree)

    def selected_medicine(self, tree):
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Select Medicine", "Pehle table se medicine select karein.")
            return None
        name = tree.item(selection[0], "values")[0]
        return next((m for m in self.medicines if m.get("name") == name), None)

    def edit_selected(self, tree):
        med = self.selected_medicine(tree)
        if med:
            self.show_medicine_form(med)

    def delete_selected(self, tree):
        med = self.selected_medicine(tree)
        if med and messagebox.askyesno(
            "Confirm Delete",
            f'{med["name"]} ko inventory se permanently delete karna hai?'
        ):
            self.medicines.remove(med)
            if self.persist_medicines():
                messagebox.showinfo("Deleted", f'{med["name"]} inventory se delete ho gayi.')
                self.show_inventory()
            else:
                # Save fail ho to medicine ko memory mein wapas rakhein.
                self.medicines.append(med)

    def show_add_medicine(self):
        self.show_medicine_form(None)

    def show_medicine_form(self, medicine=None):
        self.clear_content()
        editing = medicine is not None
        self.page_title("Edit Medicine" if editing else "Add New Medicine",
                        "Medicine ki details fill karein aur Save par click karein.")
        panel = tk.Frame(self.content, bg="white", padx=26, pady=24,
                         highlightbackground="#E2E8F0", highlightthickness=1)
        panel.pack(anchor="nw", fill="x")
        fields = [
            ("Medicine Name", "name", medicine.get("name", "") if editing else ""),
            ("Purchase Price (Rs.)", "purchase_price", str(medicine.get("purchase_price", 0)) if editing else ""),
            ("Sale Price (Rs.)", "price", str(medicine.get("price", 0)) if editing else ""),
            ("Quantity", "quantity", str(medicine.get("quantity", 0)) if editing else ""),
            ("Expiry Date (YYYY-MM-DD)", "expiry", medicine.get("expiry", "") if editing else ""),
        ]
        vars_ = {}
        for i, (label, key, value) in enumerate(fields):
            tk.Label(panel, text=label, bg="white", fg="#344054",
                     font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky="w", pady=10, padx=(0, 25))
            var = tk.StringVar(value=value)
            vars_[key] = var
            ttk.Entry(panel, textvariable=var, width=42).grid(row=i, column=1, sticky="ew", pady=10, ipady=4)
        panel.columnconfigure(1, weight=1)

        def save():
            name = vars_["name"].get().strip()
            if not name:
                messagebox.showerror("Validation", "Medicine name zaroor likhein.")
                return
            existing = next((m for m in self.medicines
                             if m.get("name", "").lower() == name.lower() and m is not medicine), None)
            if existing:
                messagebox.showerror("Duplicate", "Is naam ki medicine pehle se mojood hai.")
                return
            try:
                purchase = float(vars_["purchase_price"].get())
                price = float(vars_["price"].get())
                quantity = int(vars_["quantity"].get())
                expiry = datetime.strptime(vars_["expiry"].get().strip(), "%Y-%m-%d").date()
                if purchase <= 0 or price <= 0 or quantity < 0:
                    raise ValueError
                if expiry < date.today():
                    messagebox.showerror("Expiry Date", "Expiry date guzar chuki hai.")
                    return
            except ValueError:
                messagebox.showerror("Invalid Details", "Prices positive numbers, quantity whole number aur expiry YYYY-MM-DD mein likhein.")
                return
            record = {"name": name, "purchase_price": purchase, "price": price,
                      "quantity": quantity, "expiry": expiry.isoformat()}
            if editing:
                medicine.update(record)
            else:
                self.medicines.append(record)
            if self.persist_medicines():
                messagebox.showinfo("Saved", "Medicine successfully save ho gayi.")
                self.show_inventory()

        buttons = tk.Frame(panel, bg="white")
        buttons.grid(row=len(fields), column=1, sticky="w", pady=(20, 0))
        tk.Button(buttons, text="Save Medicine", command=save, bg="#0F9D78", fg="white",
                  relief="flat", padx=20, pady=10).pack(side="left", padx=(0, 8))
        tk.Button(buttons, text="Cancel", command=self.show_inventory, bg="#E8EEF5",
                  fg="#344054", relief="flat", padx=20, pady=10).pack(side="left")

    def persist_medicines(self):
        try:
            save_json(MEDICINES_FILE, self.medicines)
            return True
        except OSError as exc:
            messagebox.showerror("Save Error", f"Medicine data save nahi hua:\n{exc}")
            return False

    def persist_sales(self):
        try:
            save_json(SALES_FILE, self.sales)
            return True
        except OSError as exc:
            messagebox.showerror("Save Error", f"Sales data save nahi hui:\n{exc}")
            return False

    def medicine_options(self):
        return [m.get("name", "") for m in self.medicines]

    def show_sell(self):
        self.clear_content()
        self.page_title("Sell Medicine", "Medicine select karein, quantity enter karein aur bill banayein.")
        panel = tk.Frame(self.content, bg="white", padx=25, pady=22,
                         highlightbackground="#E2E8F0", highlightthickness=1)
        panel.pack(anchor="nw", fill="x")
        name_var = tk.StringVar()
        qty_var = tk.StringVar(value="1")
        total_var = tk.StringVar(value="Total: Rs. 0.00")
        tk.Label(panel, text="Medicine", bg="white", fg="#344054",
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)

        # Stable autocomplete: typing entry ka focus nahi chhorti.
        # Suggestions alag popup mein update hoti hain, is liye har harf par
        # dropdown band nahi hoti aur multi-word search bhi kaam karta hai.
        combo = ttk.Entry(panel, textvariable=name_var, width=41)
        combo.grid(row=0, column=1, sticky="w", pady=10, ipady=4)

        suggestion_popup = tk.Toplevel(self.root)
        suggestion_popup.withdraw()
        suggestion_popup.overrideredirect(True)
        suggestion_popup.attributes("-topmost", True)
        suggestion_list = tk.Listbox(
            suggestion_popup, height=8, font=("Segoe UI", 10),
            activestyle="none", exportselection=False, takefocus=False,
            bg="white", fg="#1F2937", selectbackground="#DCEAFE",
            selectforeground="#14233B", highlightthickness=1,
            highlightbackground="#CBD5E1", relief="solid", bd=1
        )
        suggestion_list.pack(fill="both", expand=True)

        def hide_suggestions():
            if suggestion_popup.winfo_exists():
                suggestion_popup.withdraw()

        def choose_suggestion(event=None):
            selected_rows = suggestion_list.curselection()
            if not selected_rows:
                return "break"
            chosen = suggestion_list.get(selected_rows[0])
            name_var.set(chosen)
            hide_suggestions()
            combo.focus_set()
            combo.icursor(tk.END)
            calculate()
            return "break"

        def update_suggestions(*_):
            typed = name_var.get().strip().casefold()
            if not typed:
                hide_suggestions()
                return

            matches = [
                medicine_name for medicine_name in self.medicine_options()
                if typed in medicine_name.casefold()
            ]
            suggestion_list.delete(0, tk.END)
            for medicine_name in matches[:100]:
                suggestion_list.insert(tk.END, medicine_name)

            if not matches or not combo.winfo_ismapped():
                hide_suggestions()
                return

            suggestion_list.configure(height=min(len(matches), 8))
            self.root.update_idletasks()
            x = combo.winfo_rootx()
            y = combo.winfo_rooty() + combo.winfo_height()
            width = max(combo.winfo_width(), 280)
            height = min(len(matches), 8) * 27 + 4
            suggestion_popup.geometry(f"{width}x{height}+{x}+{y}")
            suggestion_popup.deiconify()
            suggestion_popup.lift()

        def move_suggestion(event):
            count = suggestion_list.size()
            if count == 0:
                return "break"
            current = suggestion_list.curselection()
            index = current[0] if current else -1
            if event.keysym == "Down":
                index = min(index + 1, count - 1)
            else:
                index = max(index - 1, 0)
            suggestion_list.selection_clear(0, tk.END)
            suggestion_list.selection_set(index)
            suggestion_list.activate(index)
            suggestion_list.see(index)
            return "break"

        suggestion_list.bind("<ButtonRelease-1>", lambda event: suggestion_list.after_idle(choose_suggestion))
        combo.bind("<Down>", move_suggestion)
        combo.bind("<Up>", move_suggestion)
        combo.bind("<Return>", choose_suggestion)
        combo.bind("<Escape>", lambda event: (hide_suggestions(), "break")[1])
        tk.Label(panel, text="Quantity", bg="white", fg="#344054",
                 font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        ttk.Entry(panel, textvariable=qty_var, width=42).grid(row=1, column=1, sticky="w", pady=10, ipady=4)
        tk.Label(panel, textvariable=total_var, bg="white", fg="#0F9D78",
                 font=("Segoe UI", 16, "bold")).grid(row=2, column=1, sticky="w", pady=12)

        def selected():
            return next((m for m in self.medicines if m.get("name") == name_var.get()), None)
        def calculate(*_):
            med = selected()
            try:
                qty = int(qty_var.get())
                total_var.set(f'Total: Rs. {qty * float(med["price"]):,.2f}' if med and qty > 0 else "Total: Rs. 0.00")
            except (ValueError, TypeError, KeyError):
                total_var.set("Total: Rs. 0.00")
        name_var.trace_add("write", update_suggestions)
        name_var.trace_add("write", calculate)
        combo.bind("<FocusOut>", lambda event: combo.after(180, hide_suggestions))
        qty_var.trace_add("write", calculate)

        def sell():
            med = selected()
            if not med:
                messagebox.showerror("Select Medicine", "Medicine select karein.")
                return
            try:
                qty = int(qty_var.get())
                if qty <= 0 or qty > int(med.get("quantity", 0)):
                    raise ValueError
            except ValueError:
                messagebox.showerror("Quantity", "Quantity available stock se zyada nahi aur zero se bari honi chahiye.")
                return
            status = expiry_status(med)
            if status != "Theek":
                messagebox.showerror("Expiry Warning", f"Sale roki gayi: {status}")
                return
            total = round(qty * float(med["price"]), 2)
            if not messagebox.askyesno("Confirm Sale", f'{med["name"]}\nQuantity: {qty}\nTotal: Rs. {total:,.2f}\n\nSale confirm karein?'):
                return
            old_qty = med["quantity"]
            med["quantity"] -= qty
            bill_no = f'BILL-{len(self.sales) + 1:04d}'
            sale = {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "bill_no": bill_no, "medicine": med["name"], "quantity": qty,
                    "unit_price": med["price"], "total": total}
            self.sales.append(sale)
            if not self.persist_medicines() or not self.persist_sales():
                med["quantity"] = old_qty
                if self.sales and self.sales[-1] is sale:
                    self.sales.pop()
                self.persist_medicines()
                return
            messagebox.showinfo("Sale Complete", f"Sale successful!\nBill No: {bill_no}\nTotal: Rs. {total:,.2f}")
            self.generate_receipt(sale)
            self.show_sell()

        tk.Button(panel, text="Complete Sale & Generate Bill", command=sell,
                  bg="#0F9D78", fg="white", relief="flat", padx=20, pady=11).grid(row=3, column=1, sticky="w", pady=16)

    def generate_receipt(self, sale):
        safe_pharmacy_name = html.escape(str(self.settings.get("name") or APP_NAME))
        safe_bill = html.escape(str(sale["bill_no"]))
        safe_med = html.escape(str(sale["medicine"]))
        total = float(sale["total"])
        html_file = DATA_DIR / f'receipt_{sale["bill_no"]}.html'
        content = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{safe_pharmacy_name} Bill</title>
<style>body{{font-family:Arial;background:#f1f4f8;padding:30px}}.bill{{max-width:650px;margin:auto;background:white;padding:35px;border:1px solid #ddd}}h2,p{{text-align:center}}table{{width:100%;border-collapse:collapse;margin-top:25px}}td,th{{padding:12px;border-bottom:1px solid #ddd;text-align:left}}.right{{text-align:right}}.total{{text-align:right;font-size:23px;font-weight:bold;margin-top:25px}}button{{padding:12px 20px;margin:25px auto;display:block}}@media print{{button{{display:none}}body{{background:white}}}}</style></head><body>
<div class="bill"><h2>{safe_pharmacy_name}</h2><p>CUSTOMER SALES RECEIPT</p><hr>
<p>
Bill No: {safe_bill}<br>
Date: {html.escape(str(sale["date"]).split(" ")[0])}<br>
Time: {html.escape(str(sale["date"]).split(" ")[1])}
</p>
<table><tr><th>Medicine</th><th class="right">Qty</th><th class="right">Unit Price</th><th class="right">Total</th></tr>
<tr><td>{safe_med}</td><td class="right">{sale["quantity"]}</td><td class="right">Rs. {sale["unit_price"]:.2f}</td><td class="right">Rs. {total:.2f}</td></tr></table>
<div class="total">TOTAL: Rs. {total:.2f}</div><hr><p>Thank you for shopping!</p><button onclick="window.print()">Print Bill / Save PDF</button></div></body></html>"""
        try:
            html_file.write_text(content, encoding="utf-8")
            webbrowser.open(html_file.resolve().as_uri())
        except OSError as exc:
            messagebox.showwarning("Receipt", f"Sale save ho gayi, lekin receipt file nahi ban saki:\n{exc}")
            
    def show_stock_in(self):
        self.clear_content()
        self.page_title("Stock In", "Medicine search karein aur stock quantity add karein.")

        panel = tk.Frame(self.content, bg="white", padx=25, pady=22,
                         highlightbackground="#E2E8F0", highlightthickness=1)
        panel.pack(anchor="nw", fill="x")

        name = tk.StringVar()
        qty = tk.StringVar(value="1")
        all_medicines = self.medicine_options()

        tk.Label(panel, text="Search Medicine", bg="white").grid(
            row=0, column=0, sticky="w", pady=10
        )

        combo = ttk.Combobox(
            panel, textvariable=name, values=all_medicines,
            state="normal", width=38
        )
        combo.grid(row=0, column=1, sticky="w", pady=10, ipady=4)

        def search_medicine(event=None):
            typed = name.get().strip().casefold()
            matches = [
                medicine for medicine in all_medicines
                if typed in medicine.casefold()
            ]
            combo["values"] = matches if typed else all_medicines

        combo.bind("<KeyRelease>", search_medicine)

        tk.Label(panel, text="Quantity to Add", bg="white").grid(
            row=1, column=0, sticky="w", pady=10
        )
        ttk.Entry(panel, textvariable=qty, width=42).grid(
            row=1, column=1, sticky="w", pady=10, ipady=4
        )

        def add():
            med = next(
                (m for m in self.medicines if m.get("name") == name.get()),
                None
            )
            try:
                amount = int(qty.get())
                if not med or amount <= 0 or expiry_status(med) == "EXPIRED":
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Details",
                    "Medicine select karein aur positive quantity likhein. "
                    "Expired medicine ka stock add nahi ho sakta."
                )
                return

            old = med["quantity"]
            med["quantity"] += amount

            if self.persist_medicines():
                messagebox.showinfo(
                    "Stock Updated", f'Naya stock: {med["quantity"]}'
                )
                self.show_inventory()
            else:
                med["quantity"] = old

        tk.Button(
            panel, text="Add Stock", command=add,
            bg="#2563EB", fg="white", relief="flat",
            padx=20, pady=10
        ).grid(row=2, column=1, sticky="w", pady=15)

    def show_low_stock(self):
        self.clear_content()
        self.page_title("Low Stock Alert", f"Medicines with stock at or below {LOW_STOCK_LIMIT}.")
        tree = self.make_table(self.content, ("name", "price", "quantity", "expiry", "status"))
        rows = [m for m in self.medicines if int(m.get("quantity", 0)) <= LOW_STOCK_LIMIT]
        self.refresh_inventory_table(tree, rows)

    def show_expiry(self):
        self.clear_content()
        self.page_title("Expiry Report", "Expired medicines and medicines expiring within 30 days.")
        tree = self.make_table(self.content, ("name", "price", "quantity", "expiry", "status"))
        rows = [m for m in self.medicines if expiry_status(m) != "Theek"]
        self.refresh_inventory_table(tree, rows)

    def show_sales(self):
        self.clear_content()
        self.page_title("Sales History", "All recorded medicine sales.")
        tree = self.make_table(self.content, ("date", "bill_no", "medicine", "quantity", "unit_price", "total"),
                               {"date":"Date / Time", "bill_no":"Bill No", "medicine":"Medicine",
                                "quantity":"Qty", "unit_price":"Unit Price", "total":"Total"})
        for sale in reversed(self.sales):
            tree.insert("", "end", values=(sale.get("date", ""), sale.get("bill_no", ""),
                sale.get("medicine", ""), sale.get("quantity", 0),
                sale.get("unit_price", 0), sale.get("total", 0)))
        total = sum(float(s.get("total", 0)) for s in self.sales)
        tk.Label(self.content, text=f"Recorded Sales Total: Rs. {total:,.2f}",
                 bg="#F3F6FA", fg="#0F9D78", font=("Segoe UI", 13, "bold")).pack(anchor="e", pady=12)

    def show_report(self):
        self.clear_content()
        self.page_title("Inventory Report", "Current stock valuation and summary.")
        units = sum(int(m.get("quantity", 0)) for m in self.medicines)
        purchase = sum(int(m.get("quantity", 0)) * float(m.get("purchase_price", 0)) for m in self.medicines)
        retail = sum(int(m.get("quantity", 0)) * float(m.get("price", 0)) for m in self.medicines)
        for title, value, color in [
            ("Different Medicines", len(self.medicines), "#2563EB"),
            ("Total Units", units, "#0F9D78"),
            ("Purchase Value", f"Rs. {purchase:,.2f}", "#7C3AED"),
            ("Potential Sale Value", f"Rs. {retail:,.2f}", "#D97706"),
        ]:
            self.card(self.content, title, value, color).pack(fill="x", pady=7)

    def exit_app(self):
        if messagebox.askyesno("Exit", "Al-Shifa Pharmacy band karna hai?"):
            self.root.destroy()


def main():
    root = tk.Tk()
    PharmacyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()