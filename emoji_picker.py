#!/usr/bin/env python3
"""
Simple Emoji Picker - A command-line tool that opens a window to choose emojis to copy to clipboard.
Uses GTK with PyGObject for native Linux GUI with dark theme.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# GTK imports
try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, GLib, Gio
    GTK_AVAILABLE = True
except ImportError:
    GTK_AVAILABLE = False
    print("Error: GTK not available. Please install PyGObject to use this program.")
    print("Ubuntu/Debian: sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-4.0")
    sys.exit(1)

class EmojiPickerWindow(Gtk.ApplicationWindow):
    """GTK window for emoji picker."""
    
    def __init__(self, app):
        super().__init__(application=app)
        self.selected_emoji = None
        
        # Add caching for emoji data
        self._emoji_cache = None
        self._all_emojis_cache = None
        
        # Window setup
        self.set_title("🎨 Emoji Picker")
        self.set_default_size(800, 600)
        self.set_resizable(True)
        self.set_modal(False)  # Allow interaction with other windows
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Create the UI
        self.setup_ui()
        
        # Connect signals
        self.connect("close-request", self.on_window_close)
        
        # Try to center the window before showing it
        self.try_center_window()
        
        # Focus the window
        self.present()
        self.grab_focus()
    
    def try_center_window(self):
        """Try to center the window before it's shown."""
        try:
            display = Gdk.Display.get_default()
            if display:
                # Get the primary monitor (usually the main display)
                primary_monitor = display.get_primary_monitor()
                if primary_monitor:
                    geometry = primary_monitor.get_geometry()
                    print(f"Primary monitor geometry: {geometry.x}, {geometry.y}, {geometry.width}x{geometry.height}")
                    
                    # Get window size
                    window_width = 800
                    window_height = 600
                    
                    # Calculate center position
                    x = geometry.x + (geometry.width - window_width) // 2
                    y = geometry.y + (geometry.height - window_height) // 2
                    
                    print(f"Centering window at: ({x}, {y})")
                    
                    # Store the position for later use
                    self._center_x = x
                    self._center_y = y
                    
                    # Try to set the window position using the surface after the window is shown
                    GLib.timeout_add(200, self._apply_center_position)
                    
                    return
                
                print("No primary monitor found, using default position")
            else:
                print("Could not get display, using default position")
        except Exception as e:
            print(f"Error centering window: {e}, using default position")
    
    def _apply_center_position(self):
        """Apply the center position to the window."""
        try:
            if hasattr(self, '_center_x') and hasattr(self, '_center_y'):
                # Use xdotool to move the window to the center position
                import subprocess
                try:
                    # Wait a bit for the window to be fully shown, then move it
                    subprocess.run(['xdotool', 'search', '--name', '🎨 Emoji Picker', 'windowmove', str(self._center_x), str(self._center_y)], 
                                 capture_output=True, timeout=3)
                    print(f"Successfully moved window to center position ({self._center_x}, {self._center_y})")
                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    print(f"xdotool failed: {e}")
                except Exception as e:
                    print(f"Error using xdotool: {e}")
            else:
                print("Center position not set")
        except Exception as e:
            print(f"Error applying center position: {e}")
        
        return False  # Don't repeat
    
    def center_window(self, widget=None):
        """Center the window on screen."""
        # Use a timeout to center the window after it's fully realized
        GLib.timeout_add(100, self._do_center_window)
    
    def _do_center_window(self):
        """Actually center the window after it's shown."""
        # This is now a fallback method
        print("Fallback centering attempt")
        return False  # Don't repeat
    
    def apply_dark_theme(self):
        """Apply dark theme to the window."""
        # Create a CSS provider for dark theme
        css_provider = Gtk.CssProvider()
        # Apply dark theme CSS
        css_data = """
        window {
            background-color: #2d2d2d;
            color: #ffffff;
        }
        
        .emoji-button {
            background-color: #3d3d3d;
            border: 1px solid #555555;
            border-radius: 8px;
            padding: 8px;
            margin: 2px;
            font-size: 40px;
            min-width: 60px;
            min-height: 60px;
        }
        
        .emoji-button:hover {
            background-color: #4d4d4d;
            border-color: #777777;
        }
        
        .emoji-button:active {
            background-color: #5d5d5d;
        }
        
        .search-entry {
            background-color: #3d3d3d;
            border: 1px solid #555555;
            border-radius: 6px;
            padding: 8px;
            color: #ffffff;
            font-size: 14px;
        }
        
        .search-entry:focus {
            border-color: #777777;
        }
        
        .status-label {
            background-color: #3d3d3d;
            border: 1px solid #555555;
            border-radius: 6px;
            padding: 8px;
            color: #ffffff;
            font-size: 14px;
        }
        
        notebook {
            background-color: #2d2d2d;
        }
        
        notebook tab {
            background-color: #3d3d3d;
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 6px 6px 0 0;
        }
        
        notebook tab:checked {
            background-color: #4d4d4d;
        }
        """
        css_provider.load_from_data(css_data.encode())
        
        # Apply the CSS to the window
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main container - use expand to fill available space
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        
        # Configure main box to expand
        main_box.set_vexpand(True)
        main_box.set_hexpand(True)
        
        # Search entry - fixed height
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        search_label = Gtk.Label(label="🔍 Search:")
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Type to search emojis and press Enter...")
        # Use modern GTK 4 styling approach
        self.search_entry.add_css_class("search-entry")
        self.search_entry.connect("activate", self.on_search_activated)  # Changed from "changed" to "activate"
        search_box.append(search_label)
        search_box.append(self.search_entry)
        main_box.append(search_box)
        
        # Notebook for tabs - make it expand to fill available space
        self.notebook = Gtk.Notebook()
        self.notebook.set_vexpand(True)  # Make it expand vertically
        self.notebook.set_hexpand(True)  # Make it expand horizontally
        
        # Recent emojis tab
        recent_label = Gtk.Label(label="⭐ Recent")
        
        # Create a container for the recent emojis that expands
        recent_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        recent_container.set_vexpand(True)
        recent_container.set_hexpand(True)
        
        self.recent_grid = Gtk.Grid()
        self.recent_grid.set_row_spacing(5)
        self.recent_grid.set_column_spacing(5)
        self.recent_grid.set_vexpand(True)  # Make grid expand
        self.recent_grid.set_hexpand(True)  # Make grid expand horizontally too
        
        # Create a scrolled window for recent emojis
        self.recent_scroll = Gtk.ScrolledWindow()
        self.recent_scroll.set_child(self.recent_grid)
        self.recent_scroll.set_vexpand(True)  # Make scroll expand
        self.recent_scroll.set_hexpand(True)  # Make scroll expand horizontally
        self.recent_scroll.set_min_content_height(400)  # Set minimum height
        self.recent_scroll.set_min_content_width(600)   # Set minimum width
        
        recent_container.append(self.recent_scroll)
        self.notebook.append_page(recent_container, recent_label)
        
        # All emojis tab
        all_label = Gtk.Label(label="😀 All Emojis")
        
        # Create a container for all emojis that expands
        all_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        all_container.set_vexpand(True)
        all_container.set_hexpand(True)
        
        self.all_grid = Gtk.Grid()
        self.all_grid.set_row_spacing(5)
        self.all_grid.set_column_spacing(5)
        self.all_grid.set_vexpand(True)  # Make grid expand
        self.all_grid.set_hexpand(True)  # Make grid expand horizontally too
        
        # Create a scrolled window for all emojis
        self.all_scroll = Gtk.ScrolledWindow()
        self.all_scroll.set_child(self.all_grid)
        self.all_scroll.set_vexpand(True)  # Make scroll expand
        self.all_scroll.set_hexpand(True)  # Make scroll expand horizontally
        self.all_scroll.set_min_content_height(400)  # Set minimum height
        self.all_scroll.set_min_content_width(600)   # Set minimum width
        
        all_container.append(self.all_scroll)
        self.notebook.append_page(all_container, all_label)
        
        # Add notebook to main box - it will expand to fill available space
        main_box.append(self.notebook)
        
        # Status bar - fixed height at bottom
        self.status_label = Gtk.Label(label="Ready - Click an emoji to copy to clipboard")
        self.status_label.add_css_class("status-label")
        self.status_label.set_margin_top(5)
        main_box.append(self.status_label)
        
        # Set the main widget
        self.set_child(main_box)
        
        # Populate emojis
        self.populate_emojis()
    
    def populate_emojis(self):
        """Populate the emoji grids."""
        # Populate recent emojis
        self.populate_recent_emojis()
        
        # Populate all emojis
        self.populate_all_emojis()
    
    def populate_recent_emojis(self):
        """Populate the recent emojis grid."""
        # Clear existing widgets
        for child in self.recent_grid:
            self.recent_grid.remove(child)
        
        # Load recent emojis from file
        recent_emojis = self.load_recent_emojis()
        
        if not recent_emojis:
            label = Gtk.Label(label="No recent emojis")
            self.recent_grid.attach(label, 0, 0, 1, 1)
            return
        
        # Create emoji buttons - use more columns for wider layout
        cols = 15  # Increased from 10 to 15 columns
        for i, emoji_char in enumerate(recent_emojis):
            row = i // cols
            col = i % cols
            
            button = Gtk.Button(label=emoji_char)
            button.set_size_request(50, 50)
            button.connect("clicked", self.on_emoji_clicked, emoji_char)
            button.add_css_class("emoji-button")
            
            self.recent_grid.attach(button, col, row, 1, 1)
    
    def populate_all_emojis(self):
        """Populate the all emojis grid."""
        # Clear existing widgets
        for child in self.all_grid:
            self.all_grid.remove(child)
        
        # Create emoji buttons - use more columns for wider layout
        cols = 15  # Increased from 10 to 15 columns
        for i, emoji_data in enumerate(self.get_all_emojis()):
            row = i // cols
            col = i % cols
            
            emoji_char = emoji_data['char']
            button = Gtk.Button(label=emoji_char)
            button.set_size_request(50, 50)
            button.connect("clicked", self.on_emoji_clicked, emoji_char)
            button.add_css_class("emoji-button")
            
            self.all_grid.attach(button, col, row, 1, 1)
    
    def on_emoji_clicked(self, button, emoji_char):
        """Handle emoji button clicks."""
        try:
            self.selected_emoji = emoji_char
            print(f"Emoji clicked: {emoji_char}")
            
            # Update status immediately to show response
            self.status_label.set_text(f"Copying {emoji_char}...")
            
            # Use a timeout to perform clipboard operation asynchronously
            GLib.timeout_add(10, self._copy_emoji_async, emoji_char)
            
        except Exception as e:
            print(f"Error handling emoji click: {e}")
            self.status_label.set_text("❌ Error handling emoji click")
    
    def _copy_emoji_async(self, emoji_char):
        """Copy emoji to clipboard asynchronously."""
        try:
            # Copy to clipboard with timeout
            if self.copy_to_clipboard(emoji_char):
                # Add to recent
                self.add_to_recent(emoji_char)
                # Update status to show emoji was copied
                self.status_label.set_text(f"✅ {emoji_char} copied to clipboard!")
                # Show notification
                self.show_notification(f"Copied {emoji_char} to clipboard")
                # Refresh the recent emojis display
                self.populate_recent_emojis()
                # Reset status after 2 seconds
                GLib.timeout_add_seconds(2, self.reset_status_label)
            else:
                self.status_label.set_text("❌ Error copying emoji")
        except Exception as e:
            print(f"Error in async copy: {e}")
            self.status_label.set_text("❌ Error copying emoji")
        
        return False  # Don't repeat
    
    def reset_status_label(self):
        """Reset the status label to default text."""
        self.status_label.set_text("Ready - Click an emoji to copy to clipboard")
        return False  # Don't repeat
    
    def on_search_activated(self, entry):
        """Handle search when Enter is pressed."""
        search_text = entry.get_text().lower()
        self.filter_emojis(search_text)
    
    def filter_emojis(self, search_text):
        """Filter emojis based on search text."""
        # Clear all emojis grid
        for child in self.all_grid:
            self.all_grid.remove(child)
        
        if not search_text:
            # Show all emojis
            self.populate_all_emojis()
            return
        
        # Split search text into individual words
        search_words = search_text.lower().split()
        
        # Filter emojis with whole word matching
        cols = 15  # Match the column count used in populate_all_emojis
        filtered_count = 0
        
        for i, emoji_data in enumerate(self.get_all_emojis()):
            # Get the searchable text fields
            name = emoji_data['name'].lower()
            slug = emoji_data['slug'].lower()
            group = emoji_data['group'].lower()
            
            # Check if all search words match in any of the fields
            matches = True
            for word in search_words:
                # Check if the word appears in name, slug, or group
                if (word in name or word in slug or word in group):
                    continue
                else:
                    matches = False
                    break
            
            if matches:
                row = filtered_count // cols
                col = filtered_count % cols
                
                emoji_char = emoji_data['char']
                button = Gtk.Button(label=emoji_char)
                button.set_size_request(50, 50)
                button.connect("clicked", self.on_emoji_clicked, emoji_char)
                button.add_css_class("emoji-button")
                
                self.all_grid.attach(button, col, row, 1, 1)
                filtered_count += 1
        
        if filtered_count == 0:
            # Calculate the row position for the bottom of the grid
            estimated_rows = 20  # Adjust this based on your window size
            label = Gtk.Label(label=f"No emojis found for '{search_text}'")
            self.all_grid.attach(label, 0, estimated_rows - 1, cols, 1)  # Place at bottom row
    
    def on_window_close(self, window):
        """Handle window close event."""
        self.close()
        return False  # Allow window to close
    
    def load_recent_emojis(self):
        """Load recent emojis from file."""
        config_dir = Path.home() / ".emoji_picker"
        config_dir.mkdir(exist_ok=True)
        recent_file = config_dir / "recent_emojis.json"
        
        if recent_file.exists():
            try:
                with open(recent_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def save_recent_emojis(self, recent_emojis):
        """Save recent emojis to file."""
        config_dir = Path.home() / ".emoji_picker"
        config_dir.mkdir(exist_ok=True)
        recent_file = config_dir / "recent_emojis.json"
        
        with open(recent_file, 'w') as f:
            json.dump(recent_emojis, f, indent=2)
    
    def add_to_recent(self, emoji_char):
        """Add emoji to recent list."""
        recent_emojis = self.load_recent_emojis()
        
        if emoji_char in recent_emojis:
            recent_emojis.remove(emoji_char)
        recent_emojis.insert(0, emoji_char)
        
        # Keep only 20 items
        recent_emojis = recent_emojis[:20]
        self.save_recent_emojis(recent_emojis)
    
    def load_emoji_data(self):
        """Load emoji data from JSON file."""
        try:
            # Try to load from the same directory as the script
            script_dir = Path(__file__).parent
            emoji_file = script_dir / "emoji.json"
            
            # If not found in script directory, try current working directory
            if not emoji_file.exists():
                emoji_file = Path("emoji.json")
            
            if emoji_file.exists():
                with open(emoji_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Error: emoji.json not found at {emoji_file}")
                return {}
        except Exception as e:
            print(f"Error loading emoji data: {e}")
            return {}
    
    def get_all_emojis(self):
        """Get all available emojis from JSON file with caching."""
        # Return cached data if available
        if self._all_emojis_cache is not None:
            return self._all_emojis_cache
        
        emoji_data = self.load_emoji_data()
        
        if not emoji_data:
            print("No emoji data loaded")
            self._all_emojis_cache = []
            return []
        
        # Convert JSON data to the expected format
        emojis = []
        for emoji_char, emoji_info in emoji_data.items():
            # Create search text from name, slug, and group
            search_text = f"{emoji_info.get('name', '')} {emoji_info.get('slug', '')} {emoji_info.get('group', '')}".lower()
            
            emojis.append({
                'char': emoji_char,
                'name': emoji_info.get('name', ''),
                'slug': emoji_info.get('slug', ''),
                'group': emoji_info.get('group', ''),
                'search_text': search_text
            })
        
        # Cache the result
        self._all_emojis_cache = emojis
        return emojis
    
    def clear_emoji_cache(self):
        """Clear the emoji cache (useful if JSON file changes)."""
        self._emoji_cache = None
        self._all_emojis_cache = None
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard using system commands."""
        # Set DISPLAY environment variable if not set
        env = os.environ.copy()
        if 'DISPLAY' not in env:
            env['DISPLAY'] = ':0'
        
        clipboard_success = False
        
        try:
            # Try xclip first (X11) - xclip often times out but still succeeds
            process = subprocess.run(['xclip', '-selection', 'clipboard'], 
                                   input=text.encode('utf-8'), 
                                   capture_output=True, 
                                   env=env,
                                   timeout=2)  # Increased timeout slightly
            # xclip often times out but still copies successfully
            clipboard_success = True
        except subprocess.TimeoutExpired:
            # xclip timed out, but it usually still works
            clipboard_success = True
        except (FileNotFoundError, Exception) as e:
            print(f"xclip failed: {e}")
        
        if not clipboard_success:
            try:
                # Try xsel as fallback (X11)
                process = subprocess.run(['xsel', '--clipboard', '--input'], 
                                       input=text.encode('utf-8'), 
                                       capture_output=True, 
                                       env=env,
                                       timeout=1)
                if process.returncode == 0:
                    clipboard_success = True
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"xsel failed: {e}")
            except Exception as e:
                print(f"xsel error: {e}")
        
        if not clipboard_success:
            try:
                # Try wl-copy for Wayland
                process = subprocess.run(['wl-copy'], 
                                       input=text.encode('utf-8'), 
                                       capture_output=True, 
                                       env=env,
                                       timeout=1)
                if process.returncode == 0:
                    clipboard_success = True
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"wl-copy failed: {e}")
            except Exception as e:
                print(f"wl-copy error: {e}")
        
        # Return success if any method worked
        if clipboard_success:
            print("Clipboard operation successful")
            return True
        else:
            print("All clipboard methods failed")
            return False
    
    def show_notification(self, message):
        """Show a notification message."""
        # Use a timeout to show notification asynchronously
        GLib.timeout_add(50, self._show_notification_async, message)
    
    def _show_notification_async(self, message):
        """Show notification asynchronously."""
        try:
            # Try to use notify-send if available with timeout
            subprocess.run(['notify-send', 'Emoji Picker', message], 
                         capture_output=True, timeout=0.5)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to print
            print(f"Notification: {message}")
        except Exception as e:
            print(f"Notification error: {e}")
        
        return False  # Don't repeat

def main():
    """Main function."""
    if not GTK_AVAILABLE:
        print("Error: GTK not available. Please install PyGObject to use this program.")
        print("Ubuntu/Debian: sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-4.0")
        sys.exit(1)
    
    try:
        # Create GTK application
        app = Gtk.Application(application_id="com.emoji.picker")
        
        def on_activate(app):
            # Create and show the picker window
            window = EmojiPickerWindow(app)
            window.connect("close-request", lambda w: app.quit())
        
        app.connect("activate", on_activate)
        app.run(None)
        
    except Exception as e:
        print(f"Error starting emoji picker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
