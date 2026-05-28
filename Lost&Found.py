import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
from datetime import datetime
from PIL import Image, ImageTk

DB_NAME = "trackmystuff.db"
os.makedirs("images", exist_ok=True)
os.makedirs("proofs", exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Lost & Found Tables
    for table in ("lost_items", "found_items"):
        c.execute(f'''CREATE TABLE IF NOT EXISTS {table} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_name TEXT,
                        description TEXT,
                        location TEXT,
                        date TEXT,
                        contact_name TEXT,
                        contact_phone TEXT,
                        image_path TEXT,
                        status TEXT DEFAULT 'Active')''')

    # Claims Table (with description + proof etc.)
    c.execute('''CREATE TABLE IF NOT EXISTS claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    claimant_name TEXT,
                    claimant_contact TEXT,
                    description TEXT,
                    proof_image TEXT,
                    message TEXT,
                    status TEXT DEFAULT 'Pending',
                    FOREIGN KEY(item_id) REFERENCES found_items(id))''')

    # Messages Table (chat between admin and claimant)
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_id INTEGER,
                    sender TEXT,
                    message TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(claim_id) REFERENCES claims(id))''')

    conn.commit()
    conn.close()


class TrackMyStuffApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lost & Found System Automation")
        self.root.geometry("1000x650")
        self.root.configure(bg="#f0f0f0")

        self.style = ttk.Style()
        self.set_light_theme()

        top_frame = tk.Frame(root, bg="#003366")
        top_frame.pack(fill="x")
        title_label = tk.Label(top_frame, text="Lost & Found System Automation",
                               font=("Segoe UI", 18, "bold"),
                               bg="#003366", fg="white", pady=10)
        title_label.pack(side="left", padx=10, pady=6)

        # NEW: User Chat Access button (opens login popup)
        user_chat_btn = ttk.Button(top_frame, text="User Chat Access", command=self.open_user_login_popup)
        user_chat_btn.pack(side="right", padx=10, pady=10)

        tab_control = ttk.Notebook(root)
        self.tab_lost = ttk.Frame(tab_control)
        self.tab_found = ttk.Frame(tab_control)
        self.tab_search = ttk.Frame(tab_control)
        self.tab_claims = ttk.Frame(tab_control)

        tab_control.add(self.tab_lost, text="Report Lost Item")
        tab_control.add(self.tab_found, text="Report Found Item")
        tab_control.add(self.tab_search, text="Search Items")
        tab_control.add(self.tab_claims, text="Manage Claims")
        tab_control.pack(expand=1, fill="both")

        self.lost_entries = {}
        self.found_entries = {}
        self.lost_image_path = None
        self.found_image_path = None

        self.create_form(self.tab_lost, "lost_items", self.lost_entries, is_lost=True)
        self.create_form(self.tab_found, "found_items", self.found_entries, is_lost=False)
        self.create_search_tab()
        self.create_claims_tab()

    # ---------------- THEME ----------------
    def set_light_theme(self):
        self.style.theme_use("clam")
        self.style.configure(".", font=("Segoe UI", 10))
        self.style.configure("TButton", background="#003366", foreground="white", padding=6)
        self.style.map("TButton", background=[("active", "#005599")])
        self.style.configure("Treeview", background="#f0f0f0", fieldbackground="#f0f0f0", foreground="black")

    # ---------------- FORMS ----------------
    def create_form(self, parent, table, entry_dict, is_lost):
        frame = ttk.Frame(parent, padding=20)
        frame.pack(fill="both", expand=True)

        labels = ["Item Name", "Description", "Location", "Date (YYYY-MM-DD)",
                  "Contact Name", "Contact Phone"]
        for i, text in enumerate(labels):
            ttk.Label(frame, text=text).grid(row=i, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=50)
            entry.grid(row=i, column=1, pady=5)
            entry_dict[text] = entry

        upload_btn = ttk.Button(frame, text="Upload Image", command=lambda: self.upload_image(is_lost))
        upload_btn.grid(row=6, column=0, pady=10)

        save_btn = ttk.Button(frame, text="Save Item", command=lambda: self.save_item(table, entry_dict, is_lost))
        save_btn.grid(row=6, column=1, pady=10)

    def upload_image(self, is_lost):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            if is_lost:
                self.lost_image_path = file_path
            else:
                self.found_image_path = file_path
            messagebox.showinfo("Image Selected", "Image uploaded successfully.")

    def save_item(self, table, entry_dict, is_lost):
        name = entry_dict["Item Name"].get()
        desc = entry_dict["Description"].get()
        loc = entry_dict["Location"].get()
        date = entry_dict["Date (YYYY-MM-DD)"].get()
        contact_name = entry_dict["Contact Name"].get()
        contact_phone = entry_dict["Contact Phone"].get()

        if not all([name, desc, loc, date, contact_name, contact_phone]):
            messagebox.showerror("Error", "All fields are required.")
            return

        image_path = self.lost_image_path if is_lost else self.found_image_path
        saved_img_path = ""
        if image_path:
            ext = os.path.splitext(image_path)[1]
            saved_img_path = os.path.join("images", f"{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}")
            Image.open(image_path).save(saved_img_path)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(f'''INSERT INTO {table} 
                    (item_name, description, location, date, contact_name, contact_phone, image_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (name, desc, loc, date, contact_name, contact_phone, saved_img_path))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", f"Item saved successfully in {table}.")
        for entry in entry_dict.values():
            entry.delete(0, tk.END)
        if is_lost:
            self.lost_image_path = None
        else:
            self.found_image_path = None

    # ---------------- SEARCH TAB ----------------
    def create_search_tab(self):
        frame = ttk.Frame(self.tab_search, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Select Type:").grid(row=0, column=0, sticky="w", pady=5)
        self.type_selector = ttk.Combobox(frame, values=["Lost", "Found", "All"], state="readonly")
        self.type_selector.grid(row=0, column=1, pady=5)
        self.type_selector.set("All")

        ttk.Label(frame, text="Search Keyword:").grid(row=1, column=0, sticky="w", pady=5)
        self.search_entry = ttk.Entry(frame, width=50)
        self.search_entry.grid(row=1, column=1, pady=5)
        ttk.Button(frame, text="Search", command=self.search_items).grid(row=1, column=2, padx=5)

        self.result_table = ttk.Treeview(frame,
                                         columns=("ID", "Type", "Name", "Description", "Location", "Date", "Image", "Status"),
                                         show="headings")
        for col in ("ID", "Type", "Name", "Description", "Location", "Date", "Image", "Status"):
            self.result_table.heading(col, text=col)
            # give Description and Image wider space
            if col == "Description":
                self.result_table.column(col, width=300)
            elif col == "Image":
                self.result_table.column(col, width=140)
            else:
                self.result_table.column(col, width=100)
        self.result_table.grid(row=2, column=0, columnspan=4, pady=10, sticky="nsew")

        # Preview and Delete buttons
        ttk.Button(frame, text="Preview Selected Image", command=self.preview_selected_image).grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Delete Selected Record", command=self.delete_search_record).grid(row=3, column=1, pady=5)
        ttk.Button(frame, text="Claim Selected Found Item", command=self.open_claim_popup_from_button).grid(row=3, column=2, pady=5)

        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        # keep double-click as image preview
        self.result_table.bind("<Double-1>", lambda e: self.preview_selected_image())

    def search_items(self):
        item_type = self.type_selector.get()
        keyword = self.search_entry.get()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        results = []

        if item_type == "All" or item_type == "Lost":
            c.execute('''SELECT id, 'Lost' AS type, item_name, description, location, date, image_path, status
                         FROM lost_items WHERE item_name LIKE ? OR description LIKE ? OR location LIKE ?''',
                      (f"%{keyword}%",) * 3)
            results.extend(c.fetchall())

        if item_type == "All" or item_type == "Found":
            c.execute('''SELECT id, 'Found' AS type, item_name, description, location, date, image_path, status
                         FROM found_items WHERE item_name LIKE ? OR description LIKE ? OR location LIKE ?''',
                      (f"%{keyword}%",) * 3)
            results.extend(c.fetchall())

        conn.close()

        for row in self.result_table.get_children():
            self.result_table.delete(row)

        if results:
            for result in results:
                self.result_table.insert("", tk.END, values=result)
        else:
            messagebox.showinfo("Not Found", "No matching items found.")

    def open_claim_popup_from_button(self):
        """Open claim popup manually instead of double-click."""
        selected = self.result_table.selection()
        if not selected:
            messagebox.showinfo("Select Item", "Please select a found item to claim.")
            return

        item_data = self.result_table.item(selected[0], "values")
        item_type = item_data[1]
        if item_type != "Found":
            messagebox.showinfo("Notice", "Only found items can be claimed.")
            return

        # Now call claim popup logic using the currently selected item
        # We pass event-like behavior by reusing claim_item_popup but it expects selection internally.
        self.claim_item_popup(None)

    def delete_search_record(self):
        selected = self.result_table.selection()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a record to delete.")
            return

        item_data = self.result_table.item(selected[0], "values")
        item_id = item_data[0]
        item_type = item_data[1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this {item_type.lower()} item?"):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            table_name = "lost_items" if item_type == "Lost" else "found_items"

            # Delete associated claims if it's a found item
            if item_type == "Found":
                c.execute("DELETE FROM claims WHERE item_id=?", (item_id,))

            # Delete the item
            c.execute(f"DELETE FROM {table_name} WHERE id=?", (item_id,))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", f"{item_type} item deleted successfully!")
            self.search_items()  # Refresh the search results

    def preview_selected_image(self):
        selected = self.result_table.selection()
        if not selected:
            messagebox.showwarning("Select Row", "Please select a row to preview the image.")
            return
        item_data = self.result_table.item(selected[0], "values")
        image_path = item_data[6]  # Image column index

        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
            img.thumbnail((500, 500))
            img_tk = ImageTk.PhotoImage(img)

            popup = tk.Toplevel(self.root)
            popup.title("Image Preview")
            popup.geometry(f"{img_tk.width()+20}x{img_tk.height()+40}")
            frame = tk.Frame(popup, bg="white")
            frame.pack(expand=True, fill="both", padx=8, pady=8)
            lbl = tk.Label(frame, image=img_tk, bg="white")
            lbl.image = img_tk
            lbl.pack(expand=True)
        else:
            messagebox.showinfo("No Image", "No image available for this item.")

    # ---------------- CLAIM POPUP (for submitting a claim) ----------------
    def claim_item_popup(self, event):
        # Open claim using currently selected row in result_table
        selected = self.result_table.selection()
        if not selected:
            return
        item_data = self.result_table.item(selected[0], "values")
        item_type = item_data[1]
        item_id = item_data[0]

        if item_type != "Found":
            messagebox.showinfo("Notice", "You can only claim found items.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Claim Found Item")
        popup.geometry("420x440")

        ttk.Label(popup, text="Your Name:").pack(pady=5)
        name_entry = ttk.Entry(popup, width=45)
        name_entry.pack(pady=5)

        ttk.Label(popup, text="Contact Number:").pack(pady=5)
        contact_entry = ttk.Entry(popup, width=45)
        contact_entry.pack(pady=5)

        ttk.Label(popup, text="Short Description (why it's yours):").pack(pady=5)
        desc_entry = ttk.Entry(popup, width=45)
        desc_entry.pack(pady=5)

        ttk.Label(popup, text="Proof Message / Details:").pack(pady=5)
        msg_entry = tk.Text(popup, height=6, width=45)
        msg_entry.pack(pady=5)

        proof_image_path = {"path": None}  # closure variable

        def upload_proof():
            fp = filedialog.askopenfilename(parent=popup, filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if fp:
                proof_image_path["path"] = fp
                messagebox.showinfo("Uploaded", "Proof image selected.")

        ttk.Button(popup, text="Upload Proof Image", command=upload_proof).pack(pady=6)

        def submit_claim():
            name = name_entry.get().strip()
            contact = contact_entry.get().strip()
            desc = desc_entry.get().strip()
            message = msg_entry.get("1.0", tk.END).strip()

            if not all([name, contact, desc, message]):
                messagebox.showerror("Error", "All fields are required.")
                return
            if not proof_image_path["path"]:
                messagebox.showerror("Error", "Please upload a proof image.")
                return

            saved_proof = os.path.join("proofs", f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
            Image.open(proof_image_path["path"]).save(saved_proof)

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''INSERT INTO claims (item_id, claimant_name, claimant_contact, description, proof_image, message)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (item_id, name, contact, desc, saved_proof, message))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Claim submitted successfully!")
            popup.destroy()
            self.load_claims()

        ttk.Button(popup, text="Submit Claim", command=submit_claim).pack(pady=10)

    # ---------------- CLAIMS TAB ----------------
    def create_claims_tab(self):
        frame = ttk.Frame(self.tab_claims, padding=12)
        frame.pack(fill="both", expand=True)

        self.claims_table = ttk.Treeview(frame, columns=("ID", "Item ID", "Name", "Contact", "Description", "Message", "Status"), show="headings")
        for col in ("ID", "Item ID", "Name", "Contact", "Description", "Message", "Status"):
            self.claims_table.heading(col, text=col)
            self.claims_table.column(col, width=120 if col != "Description" else 250, anchor="w")
        self.claims_table.grid(row=0, column=0, columnspan=6, pady=10, sticky="nsew")

        ttk.Button(frame, text="Refresh", command=self.load_claims).grid(row=1, column=0, pady=6)
        ttk.Button(frame, text="View Proof Image", command=self.preview_proof_image).grid(row=1, column=1, pady=6)
        ttk.Button(frame, text="Chat", command=self.open_chat_for_selected).grid(row=1, column=2, pady=6)
        ttk.Button(frame, text="Approve", command=lambda: self.update_claim_status("Approved")).grid(row=1, column=3, pady=6)
        ttk.Button(frame, text="Reject", command=lambda: self.update_claim_status("Rejected")).grid(row=1, column=4, pady=6)
        ttk.Button(frame, text="Delete Claim", command=self.delete_claim).grid(row=1, column=5, pady=6)

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(2, weight=1)
        self.load_claims()

    def load_claims(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, item_id, claimant_name, claimant_contact, description, message, status FROM claims")
        claims = c.fetchall()
        conn.close()

        for row in self.claims_table.get_children():
            self.claims_table.delete(row)
        for claim in claims:
            self.claims_table.insert("", tk.END, values=claim)

    def preview_proof_image(self):
        selected = self.claims_table.selection()
        if not selected:
            messagebox.showwarning("Select Claim", "Please select a claim to view the proof image.")
            return
        claim_id = self.claims_table.item(selected[0], "values")[0]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT proof_image FROM claims WHERE id=?", (claim_id,))
        row = c.fetchone()
        conn.close()
        if row and row[0] and os.path.exists(row[0]):
            try:
                img = Image.open(row[0])
                img.thumbnail((500, 500))
                img_tk = ImageTk.PhotoImage(img)
                popup = tk.Toplevel(self.root)
                popup.title("Proof Image")
                popup.geometry(f"{img_tk.width()+20}x{img_tk.height()+40}")
                frame = tk.Frame(popup, bg="white")
                frame.pack(expand=True, fill="both", padx=8, pady=8)
                lbl = tk.Label(frame, image=img_tk, bg="white")
                lbl.image = img_tk
                lbl.pack(expand=True)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open proof image: {e}")
        else:
            messagebox.showinfo("No Proof", "No proof image available for this claim.")

    def delete_claim(self):
        selected = self.claims_table.selection()
        if not selected:
            messagebox.showwarning("Select Claim", "Please select a claim to delete.")
            return
        claim_id = self.claims_table.item(selected[0], "values")[0]
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this claim?"):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM claims WHERE id=?", (claim_id,))
            conn.commit()
            conn.close()
            self.load_claims()
            messagebox.showinfo("Deleted", "Claim deleted successfully.")

    def update_claim_status(self, new_status):
        selected = self.claims_table.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a claim.")
            return
        claim_id = self.claims_table.item(selected[0], "values")[0]
        item_id = self.claims_table.item(selected[0], "values")[1]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE claims SET status=? WHERE id=?", (new_status, claim_id))
        if new_status == "Approved":
            c.execute("UPDATE found_items SET status='Returned' WHERE id=?", (item_id,))
        elif new_status == "Rejected":
            c.execute("UPDATE found_items SET status='Active' WHERE id=?", (item_id,))
        conn.commit()
        conn.close()
        self.load_claims()
        messagebox.showinfo("Updated", f"Claim {new_status} successfully!")

    # ---------------- CHAT (Messaging) - Admin side ----------------
    def open_chat_for_selected(self):
        selected = self.claims_table.selection()
        if not selected:
            messagebox.showwarning("Select Claim", "Please select a claim to open chat.")
            return
        claim_vals = self.claims_table.item(selected[0], "values")
        claim_id = claim_vals[0]
        claimant_name = claim_vals[2]
        self.open_chat_popup(claim_id, claimant_name, allow_sender_choice=True)

    def open_chat_popup(self, claim_id, claimant_name, allow_sender_choice=False):
        popup = tk.Toplevel(self.root)
        popup.title(f"Chat - Claim #{claim_id} ({claimant_name})")
        popup.geometry("600x500")

        # Messages display
        messages_frame = ttk.Frame(popup, padding=8)
        messages_frame.pack(fill="both", expand=True)

        text = tk.Text(messages_frame, state="disabled", wrap="word")
        text.pack(fill="both", expand=True, padx=4, pady=4)

        # Input area
        input_frame = ttk.Frame(popup, padding=6)
        input_frame.pack(fill="x")

        ttk.Label(input_frame, text="Sender:").grid(row=0, column=0, sticky="w")
        if allow_sender_choice:
            sender_cb = ttk.Combobox(input_frame, values=["Admin"], state="readonly", width=10)
            sender_cb.set("Admin")
        else:
            sender_cb = ttk.Combobox(input_frame, values=["User"], state="readonly", width=10)
            sender_cb.set("User")
        sender_cb.grid(row=0, column=1, padx=6, sticky="w")

        msg_entry = tk.Text(input_frame, height=3, width=55)
        msg_entry.grid(row=1, column=0, columnspan=3, pady=6, padx=4)

        def load_messages():
            text.config(state="normal")
            text.delete("1.0", tk.END)
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT sender, message, timestamp FROM messages WHERE claim_id=? ORDER BY id", (claim_id,))
            rows = c.fetchall()
            conn.close()
            if rows:
                for s, m, ts in rows:
                    text.insert(tk.END, f"[{ts}] {s}: {m}\n\n")
            else:
                text.insert(tk.END, "No messages yet.\n\n")
            text.config(state="disabled")
            text.see(tk.END)

        def send_message():
            sender = sender_cb.get()
            message = msg_entry.get("1.0", tk.END).strip()
            if not message:
                messagebox.showwarning("Empty", "Please enter a message.")
                return
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO messages (claim_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
                      (claim_id, sender, message, ts))
            conn.commit()
            conn.close()
            msg_entry.delete("1.0", tk.END)
            load_messages()

        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=6, sticky="e")
        ttk.Button(btn_frame, text="Send", command=send_message).pack(side="right", padx=6)
        ttk.Button(btn_frame, text="Refresh", command=load_messages).pack(side="right")

        # initial load
        load_messages()

    # ---------------- USER CHAT ACCESS (pop-up login) ----------------
    def open_user_login_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("User Chat Access")
        popup.geometry("420x220")

        ttk.Label(popup, text="Enter your contact number (used in claim):").pack(pady=8)
        contact_entry = ttk.Entry(popup, width=40)
        contact_entry.pack(pady=6)

        result_frame = ttk.Frame(popup, padding=6)
        result_frame.pack(fill="both", expand=True)

        claims_list = ttk.Treeview(result_frame, columns=("Claim ID", "Item ID", "Status"), show="headings", height=6)
        for col in ("Claim ID", "Item ID", "Status"):
            claims_list.heading(col, text=col)
            claims_list.column(col, width=120)
        claims_list.pack(fill="both", expand=True, pady=6)

        def load_user_claims():
            phone = contact_entry.get().strip()
            if not phone:
                messagebox.showwarning("Input", "Please enter your contact number.")
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, item_id, status FROM claims WHERE claimant_contact=?", (phone,))
            rows = c.fetchall()
            conn.close()
            for r in claims_list.get_children():
                claims_list.delete(r)
            if rows:
                for row in rows:
                    claims_list.insert("", tk.END, values=row)
            else:
                messagebox.showinfo("No Claims", "No claims found for this contact number.")

        def open_user_chat_for_selected():
            sel = claims_list.selection()
            if not sel:
                messagebox.showwarning("Select", "Please select a claim.")
                return
            claim_id = claims_list.item(sel[0], "values")[0]

            # fetch claimant name for title
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT claimant_name FROM claims WHERE id=?", (claim_id,))
            row = c.fetchone()
            conn.close()
            claimant_name = row[0] if row else "User"
            # open chat popup with sender fixed to "User" (allow_sender_choice False)
            self.open_chat_popup(claim_id, claimant_name, allow_sender_choice=False)

        ttk.Button(popup, text="Load My Claims", command=load_user_claims).pack(pady=4)
        ttk.Button(popup, text="Open Chat For Selected Claim", command=open_user_chat_for_selected).pack(pady=4)

    # ------------- end user chat / admin chat --------------

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = TrackMyStuffApp(root)
    root.mainloop()
