#!/bin/bash

# Emoji Picker Installation Script
# This script installs the dependencies needed to run emoji_picker.py

set -e  # Exit on any error

echo "🎨 Emoji Picker - Dependency Installation"
echo "========================================"

# Detect the distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo "❌ Could not detect operating system"
    exit 1
fi

echo "�� Detected OS: $OS $VER"
echo ""

# Function to install dependencies based on distribution
install_dependencies() {
    case $OS in
        *"Ubuntu"*|*"Debian"*|*"Linux Mint"*|*"Pop!_OS"*)
            echo "🔧 Installing dependencies for Ubuntu/Debian..."
            sudo apt-get update
            sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 xclip
            echo "✅ Ubuntu/Debian dependencies installed successfully"
            ;;
        *"Fedora"*|*"Red Hat"*|*"CentOS"*|*"Rocky"*|*"AlmaLinux"*)
            echo "🔧 Installing dependencies for Fedora/RHEL/CentOS..."
            if command -v dnf &> /dev/null; then
                sudo dnf install -y python3-gobject gtk4 xclip
            else
                sudo yum install -y python3-gobject gtk4 xclip
            fi
            echo "✅ Fedora/RHEL/CentOS dependencies installed successfully"
            ;;
        *"Arch Linux"*|*"Manjaro"*)
            echo "🔧 Installing dependencies for Arch Linux..."
            sudo pacman -S --noconfirm python-gobject gtk4 xclip
            echo "✅ Arch Linux dependencies installed successfully"
            ;;
        *"openSUSE"*)
            echo "🔧 Installing dependencies for openSUSE..."
            sudo zypper install -y python3-gobject gtk4 xclip
            echo "✅ openSUSE dependencies installed successfully"
            ;;
        *"Gentoo"*)
            echo "🔧 Installing dependencies for Gentoo..."
            sudo emerge --ask dev-python/pygobject gtk4 x11-misc/xclip
            echo "✅ Gentoo dependencies installed successfully"
            ;;
        *)
            echo "⚠️  Unsupported distribution: $OS"
            echo "�� Please install the following packages manually:"
            echo "   - python3-gi or python3-gobject"
            echo "   - gir1.2-gtk-4.0 or gtk4"
            echo "   - xclip or xsel"
            echo ""
            echo "🔗 See the README.md for manual installation instructions"
            exit 1
            ;;
    esac
}

# Function to make the script executable
make_executable() {
    if [ -f "emoji_picker.py" ]; then
        echo "🔧 Making emoji_picker.py executable..."
        chmod +x emoji_picker.py
        echo "✅ emoji_picker.py is now executable"
    else
        echo "❌ emoji_picker.py not found in current directory"
        exit 1
    fi
}

# Function to test the installation
test_installation() {
    echo ""
    echo "🧪 Testing installation..."
    
    # Test Python GTK
    if python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('✅ GTK 4 is available')" 2>/dev/null; then
        echo "✅ GTK 4 Python bindings are working"
    else
        echo "❌ GTK 4 Python bindings are not working"
        echo "   Please check your installation"
        exit 1
    fi
    
    # Test clipboard tools
    if command -v xclip &> /dev/null; then
        echo "✅ xclip is available"
    elif command -v xsel &> /dev/null; then
        echo "✅ xsel is available"
    elif command -v wl-copy &> /dev/null; then
        echo "✅ wl-copy is available"
    else
        echo "⚠️  No clipboard tool found (xclip, xsel, or wl-copy)"
        echo "   Clipboard functionality may not work"
    fi
}

# Function to show usage instructions
show_usage() {
    echo ""
    echo "🎉 Installation complete!"
    echo "========================"
    echo ""
    echo "�� Usage:"
    echo "   python3 emoji_picker.py"
    echo "   or"
    echo "   ./emoji_picker.py"
    echo ""
    echo "📋 Features:"
    echo "   - Native GTK GUI with dark theme"
    echo "   - Search emojis by typing and pressing Enter"
    echo "   - Recent emojis tab"
    echo "   - Automatic clipboard copying"
    echo ""
    echo "🔧 Configuration:"
    echo "   Recent emojis are saved to ~/.emoji_picker/recent_emojis.json"
    echo ""
    echo "❓ For help, see README.md"
}

# Main installation process
main() {
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        echo "❌ Please don't run this script as root"
        echo "   Run it as a regular user"
        exit 1
    fi
    
    # Check if emoji_picker.py exists
    if [ ! -f "emoji_picker.py" ]; then
        echo "❌ emoji_picker.py not found in current directory"
        echo "   Please run this script from the emoji picker directory"
        exit 1
    fi
    
    # Install dependencies
    install_dependencies
    
    # Make script executable
    make_executable
    
    # Test installation
    test_installation
    
    # Show usage instructions
    show_usage
}

# Run the main function
main "$@"
