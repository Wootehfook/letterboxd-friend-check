"""
Setup dialog for the Letterboxd Friend Check application.
Contains class for configuring user preferences.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import logging

# Configure logging
logger = logging.getLogger(__name__)


class SetupDialog(tk.Toplevel):
    """Dialog for setting up user configuration"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Setup dialog properties
        self.title("Letterboxd User Setup")
        self.geometry("500x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")

        # Variables - inherit from parent if available
        self.username_var = tk.StringVar(
            value=parent.username.get() if parent.username.get() else ""
        )
        self.remember_user_var = tk.BooleanVar(value=parent.remember_user.get())
        self.auto_fetch_details_var = tk.BooleanVar(
            value=getattr(parent, "auto_fetch_details", True)
        )
        self.status_var = tk.StringVar()

        # Create UI
        self.create_widgets()

        # Make dialog modal
        self.wait_visibility()
        self.focus_set()

    def create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self, padding="20 10")
        main_frame.pack(fill="both", expand=True)

        # Header
        header_label = ttk.Label(
            main_frame, text="Letterboxd User Setup", font=("TkDefaultFont", 12, "bold")
        )
        header_label.pack(pady=(0, 15))

        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill="x", pady=5)

        # Username entry
        ttk.Label(input_frame, text="Letterboxd Username:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        username_entry = ttk.Entry(input_frame, textvariable=self.username_var, width=30)
        username_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        username_entry.focus_set()  # Set focus on username entry

        # Remember username checkbox
        remember_checkbox = ttk.Checkbutton(
            input_frame, text="Remember Username", variable=self.remember_user_var
        )
        remember_checkbox.grid(row=0, column=2, sticky=tk.W, pady=5)

        # Help text
        help_text = ttk.Label(
            input_frame,
            text=(
                "Enter your public Letterboxd username to compare your watchlist\n"
                "with your friends. No login required!"
            ),
            wraplength=400,
            justify="left",
            font=("TkDefaultFont", 9),
        )
        help_text.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=15)

        # Settings separator
        ttk.Separator(input_frame, orient="horizontal").grid(
            row=2, column=0, columnspan=3, sticky=tk.EW, pady=15
        )

        # Data settings
        ttk.Label(input_frame, text="Data Settings:").grid(row=3, column=0, sticky=tk.W, pady=5)
        auto_fetch_checkbox = ttk.Checkbutton(
            input_frame,
            text="Auto-fetch Movie Details during Sync",
            variable=self.auto_fetch_details_var,
        )
        auto_fetch_checkbox.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)

        # Test connection
        ttk.Button(input_frame, text="Check Username", command=self.verify_username).grid(
            row=4, column=1, sticky=tk.W, pady=15
        )

        # Status message
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="green")
        status_label.pack(fill="x", pady=10)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Save & Close", command=self.save_and_close).pack(
            side=tk.RIGHT, padx=5
        )

    def verify_username(self):
        """Verify that the Letterboxd username exists"""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter your Letterboxd username")
            return

        self.status_var.set("Checking username...")
        self.update_idletasks()

        try:
            # Test by fetching the user profile page
            session = requests.Session()
            response = session.get(f"https://letterboxd.com/{username}/")

            if response.status_code != 200:
                self.status_var.set("")
                messagebox.showerror("Error", f"Username '{username}' not found on Letterboxd")
                return

            # Check if the username is valid by checking for certain elements
            if f"<title>{username}" in response.text or f'href="/{username}/' in response.text:
                self.status_var.set(f"Username '{username}' is valid!")
                messagebox.showinfo("Success", f"Username '{username}' found on Letterboxd")
            else:
                self.status_var.set("")
                messagebox.showwarning("Warning", f"Username '{username}' might not be valid")

        except Exception as e:
            self.status_var.set("")
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def save_and_close(self):
        """Save the configuration and close the dialog"""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter your Letterboxd username")
            return

        # Update parent variables
        self.parent.username.set(username)
        self.parent.remember_user.set(self.remember_user_var.get())
        self.parent.auto_fetch_details = self.auto_fetch_details_var.get()

        # Update UI elements in parent
        self.parent.username_var.set(username)
        self.parent.setup_status_var.set("Configuration saved")
        self.parent.status_var.set("Ready to sync")

        # Enable sync tab
        self.parent.notebook.tab(1, state="normal")

        # Save config
        self.parent.save_config()

        # Close dialog
        self.destroy()
