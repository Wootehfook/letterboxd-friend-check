import tkinter as tk
import re


def refresh_movies_list(self):
    """Refresh the movies list based on the current filter settings"""
    # Get the selected friend
    selection = self.friends_listbox.curselection()
    if not selection:
        return

    # Get the selected friend
    friend_text = self.friends_listbox.get(selection[0])
    # Extract friend name without the count
    friend = friend_text.split(" (")[0]

    # Check if we should show all movies or only common movies
    show_common_only = self.show_common_only_var.get()

    # Update the movies label
    if show_common_only:
        self.movies_label.config(text=f"Movies in common with {friend}:")
    else:
        self.movies_label.config(text=f"All movies from {friend}:")

    # Clear the treeview
    for item in self.movies_tree.get_children():
        self.movies_tree.delete(item)

    # Get movies to display
    if show_common_only:
        # Show only common movies
        if friend in self.common_movies:
            movies_to_display = sorted(self.common_movies[friend])
        else:
            movies_to_display = []
    else:
        # Show all movies from this friend's watchlist
        if friend in self.friends_watchlists:
            movies_to_display = sorted(self.friends_watchlists[friend])
        else:
            movies_to_display = []

    # Apply search filter if text is entered
    if hasattr(self, "search_var") and self.search_var.get():
        search_term = self.search_var.get().lower()
        movies_to_display = [movie for movie in movies_to_display if search_term in movie.lower()]

    # Add the movies to the treeview
    for movie in movies_to_display:
        # Extract title and year if available
        title = movie
        year = ""
        match = re.search(r"(.+)\s+\((\d{4})\)$", movie)
        if match:
            title = match.group(1)
            year = match.group(2)

        # Check if this is a common movie
        is_common = friend in self.common_movies and movie in self.common_movies[friend]

        # Insert into treeview with default values for other columns
        movie_id = self.movies_tree.insert("", tk.END, values=(title, year, "—", "—", "—"))

        # Apply tag for the original movie title for reference
        if is_common:
            self.movies_tree.item(movie_id, tags=(movie, "common"))
        else:
            self.movies_tree.item(movie_id, tags=(movie,))

    # Update status
    self.status_var.set(f"{len(movies_to_display)} movies displayed")


def on_toggle_common_filter(self):
    """Handle toggling the common movies filter"""
    self.refresh_movies_list()
