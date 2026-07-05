# Balatro Replication: Coding & Environment Setup Guide
This guide provides step-by-step instructions to set up a local Python development environment on a **MacBook Pro 14" (Apple Silicon M1)** to write and run this Balatro replication.

Since you are using an **Apple Silicon (M1) Mac**, running software natively (`arm64`) instead of translated via Rosetta 2 is critical to ensure optimal performance, native OpenGL hardware acceleration (needed for Arcade/Pygame), and compatibility with native library binaries.

---

## 1. Prerequisites (System Setup)

Before installing Python, make sure you have the command-line developer tools and Homebrew installed natively.

### Step 1.1: Install Xcode Command Line Tools
Open your terminal and run:
```bash
xcode-select --install
```
*If a dialog box appears saying they are already installed, you can skip this step.*

### Step 1.2: Install Homebrew (Mac Package Manager)
Ensure Homebrew is installed natively for Apple Silicon (which installs in `/opt/homebrew/` instead of `/usr/local/` for Intel):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, verify that Homebrew is in your shell profile by running:
```bash
brew --version
```
If `brew` command is not found, add it to your path:
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc
```

---

## 2. Installing Python 3.11+ Natively

For game development with **Arcade** or **Pygame-CE**, Python 3.11 is the recommended sweet spot for compatibility and package pre-build availability on Apple Silicon.

Install Python 3.11 via Homebrew:
```bash
brew install python@3.11
```

Confirm that the installation succeeded and points to the native `arm64` version:
```bash
# Check version
python3.11 --version

# Verify native arm64 architecture
python3.11 -c "import platform; print(platform.machine())"
```
> [!IMPORTANT]
> The second command **must output `arm64`**. If it outputs `x86_64`, your terminal is running under Rosetta translation. To fix this, ensure your terminal application is NOT set to "Open using Rosetta" in its "Get Info" settings in macOS Finder.

---

## 3. Creating & Activating the Virtual Environment

Always use a virtual environment (`venv`) to keep project packages isolated and avoid messing up system/brew packages.

### Step 3.1: Navigate to Project Directory
Navigate to the root directory of the project:
```bash
cd /Users/trongkhiem/Developer/workspace/halando
```

### Step 3.2: Initialize the Virtual Environment
Create a `.venv` directory containing a native copy of your Python 3.11 installation:
```bash
python3.11 -m venv .venv
```

### Step 3.3: Activate the Virtual Environment
Activate the environment in your shell:
```bash
source .venv/bin/activate
```
*Your terminal prompt will now show `(.venv)` at the beginning.*

### Step 3.4: Upgrade Package Tools
With the virtual environment activated, upgrade core packaging tools:
```bash
pip install --upgrade pip setuptools wheel
pip install pygame-ce```

---

## 4. Installing Game Engine & Dependencies

Depending on whether you choose **Arcade** (Recommended in [overview.md](file:///Users/trongkhiem/Developer/workspace/halando/docs/overview.md)) or **Pygame-CE**, run the corresponding setup.

### Option A: Installing Arcade (Recommended)
Arcade utilizes OpenGL 3.3+ for accelerated 2D graphics, rendering card animations, and CRT/psychedelic custom shaders very efficiently on Apple Silicon.

```bash
pip install arcade
```

### Option B: Installing Pygame-CE (Community Edition)
Pygame-CE is an optimized, community-maintained fork of Pygame that compiles and runs natively on Apple Silicon.

```bash

```

### Extra: SQLite & Development Dependencies
- **SQLite Engine**: SQLite is built into Python's standard library (`sqlite3`), so **no pip installation is required** to write database code!
- **SQLite GUI Viewer**: To debug game profiles, save files, and unlocks, install **DB Browser for SQLite**:
  ```bash
  brew install --cask db-browser-for-sqlite
  ```
  *(Alternatively, you can install the **SQLite Viewer** extension directly inside VS Code).*

---

## 5. Directory Structure & Running the Game

To set up the files for running, you'll want to structure your repository like this:

```
halando/
│
├── docs/                      # Documentation folder
│   ├── overview.md
│   ├── planning.md
│   ├── screen-list.md
│   ├── core-game-logic.md
│   └── game-running-guidance.md
│
├── src/                       # Main source code directory
│   ├── main.py                # Game entry point
│   ├── engine.py              # Game engine logic
│   ├── db.py                  # Database operations (SQLite)
│   ├── ui/                    # UI elements and screens
│   └── assets/                # Audio, fonts, sprites/textures
│
├── .venv/                     # Python virtual environment (ignored by Git)
├── requirements.txt           # File listing python dependencies
└── .gitignore                 # Files and folders ignored by git
```

### Creating `requirements.txt`
In the root directory, create a `requirements.txt` listing your project packages:
```text
# Graphics Engine
arcade==3.0.0rc4  # Or specify the preferred version

# Packaging
pyinstaller
```
Then developers can install it directly by running:
```bash
pip install -r requirements.txt
```

### Running the Game Locally
With the virtual environment activated, start the application via the entry file:
```bash
python src/main.py
```

---

## 6. M1 Mac-Specific Troubleshooting & Performance Tips

### M1 Retina Display Scaling (High-DPI)
M1 Macbooks use high-resolution Retina displays. If you notice your game window looks pixelated or small:
- **For Arcade**: Arcade handles Retina displays automatically, using `window.get_pixel_ratio()` to scale coordinates properly.
- **For Pygame-CE**: When initializing the display, use the `pygame.SCALED` flag or enable high-DPI awareness:
  ```python
  import pygame
  pygame.init()
  screen = pygame.display.set_mode((width, height), pygame.SCALED | pygame.RESIZABLE)
  ```

### OpenGL Version Error (Arcade)
If Arcade fails to launch with an OpenGL version error (e.g., `arcade.window.WindowException: Cannot create an OpenGL context`):
1. Verify Python is running natively on Apple Silicon (`arm64`), not translated Intel (`x86_64`).
2. Update macOS to the latest version. Apple's native graphics drivers support OpenGL 4.1, which exceeds Arcade's requirement of 3.3.

### Virtual Environment Terminal Prompt Fix
If the virtual environment prompt `(.venv)` does not show up in your terminal after running `source .venv/bin/activate`, check your shell config (`~/.zshrc`) to ensure custom prompt engines (like Starship, Oh My Zsh, or Powerlevel10k) are not hiding it, or configure them to display the active python virtualenv.
