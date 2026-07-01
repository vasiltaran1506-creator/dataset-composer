# 🚀 Dataset Composer v1.0

**The ultimate rule-based prompt generator for Character LoRA training.**

Dataset Composer is an intelligent, modular engine designed to generate thousands of logically consistent, highly detailed image prompts for training Character LoRAs (using Kohya_ss, OneTrainer, etc.). 

Instead of relying on random tag soups, Dataset Composer uses a **3-Layer Rule Architecture** to ensure that your character is always in the right outfit, in the right location, doing the right thing, with perfect lighting.

---

## ✨ Key Features

### 🧬 1. Rule Inheritance Architecture
Stop repeating yourself. Define base rules for **Location Types** (e.g., `indoor_cultural`, `outdoor_aquatic`), and specific locations (like `library` or `beach`) will automatically inherit them.
* *Example:* `indoor_cultural.toml` globally bans pajamas and shouting. `library.toml` inherits this and only adds its unique traits (books, warm lamps).

### 🛡️ 2. Double-Filtering Engine
* **Layer 1 (Universal Laws):** TOML files define what is physically and logically possible in the world (e.g., you can't cook in a library, you need an umbrella in the rain).
* **Layer 2 (Character Soul):** A YAML profile acts as a strict whitelist. Even if the world allows a "red leather jacket", the engine will filter it out if it's not in your character's canonical wardrobe.

### 🔍 3. Smart Scene Validator
The engine doesn't just generate; it **verifies**. Before saving a prompt, the built-in Validator checks for forbidden tags and logical conflicts. If a scene fails the check, it is silently discarded and regenerated, guaranteeing a **100% clean dataset**.

### 📚 4. Atomic Prompt Library
Over 2,500+ meticulously categorized Danbooru-style tags organized into atomic `.txt` files (clothing, lighting, weather, props, camera angles).

---

## 🏗️ Architecture

```text
dataset-composer/
├── character-profile.yaml      # 👤 The Soul: Fixed traits & canonical wardrobe
├── prompt-library/             # 🧱 The Bricks: 2500+ atomic tags (.txt)
├── scene-rules/                # 📜 The Laws: TOML configuration files
│   ├── location_types/         # 🏛️ Base rules (indoor_private, transit, etc.)
│   ├── locations/              # 📍 Specific places (library, street, beach)
│   ├── actions/                # 🎬 What is happening (reading, cooking)
│   ├── weather/                # 🌦️ Atmospheric conditions (rain, fog, night)
│   └── camera/                 # 📸 Framing & angles (pov, close_up)
└── src/                        # 🧠 The Brain: Python engine
    ├── main.py                 # Entry point (Test & Generate modes)
    ├── scene_builder.py        # Core logic, merging & validation
    ├── config_loader.py        # YAML & TOML parser
    ├── prompt_library.py       # Tag indexer
    └── exporter.py             # Dataset file generator# 🚀 Dataset Composer v1.0

**The ultimate rule-based prompt generator for Character LoRA training.**

Dataset Composer is an intelligent, modular engine designed to generate thousands of logically consistent, highly detailed image prompts for training Character LoRAs (using Kohya_ss, OneTrainer, etc.). 

Instead of relying on random tag soups, Dataset Composer uses a **3-Layer Rule Architecture** to ensure that your character is always in the right outfit, in the right location, doing the right thing, with perfect lighting.

---

## ✨ Key Features

### 🧬 1. Rule Inheritance Architecture
Stop repeating yourself. Define base rules for **Location Types** (e.g., `indoor_cultural`, `outdoor_aquatic`), and specific locations (like `library` or `beach`) will automatically inherit them.
* *Example:* `indoor_cultural.toml` globally bans pajamas and shouting. `library.toml` inherits this and only adds its unique traits (books, warm lamps).

### 🛡️ 2. Double-Filtering Engine
* **Layer 1 (Universal Laws):** TOML files define what is physically and logically possible in the world (e.g., you can't cook in a library, you need an umbrella in the rain).
* **Layer 2 (Character Soul):** A YAML profile acts as a strict whitelist. Even if the world allows a "red leather jacket", the engine will filter it out if it's not in your character's canonical wardrobe.

### 🔍 3. Smart Scene Validator
The engine doesn't just generate; it **verifies**. Before saving a prompt, the built-in Validator checks for forbidden tags and logical conflicts. If a scene fails the check, it is silently discarded and regenerated, guaranteeing a **100% clean dataset**.

### 📚 4. Atomic Prompt Library
Over 2,500+ meticulously categorized Danbooru-style tags organized into atomic `.txt` files (clothing, lighting, weather, props, camera angles).

---

## 🏗️ Architecture

```text
dataset-composer/
├── character-profile.yaml      # 👤 The Soul: Fixed traits & canonical wardrobe
├── prompt-library/             # 🧱 The Bricks: 2500+ atomic tags (.txt)
├── scene-rules/                # 📜 The Laws: TOML configuration files
│   ├── location_types/         # 🏛️ Base rules (indoor_private, transit, etc.)
│   ├── locations/              # 📍 Specific places (library, street, beach)
│   ├── actions/                # 🎬 What is happening (reading, cooking)
│   ├── weather/                # 🌦️ Atmospheric conditions (rain, fog, night)
│   └── camera/                 # 📸 Framing & angles (pov, close_up)
└── src/                        # 🧠 The Brain: Python engine
    ├── main.py                 # Entry point (Test & Generate modes)
    ├── scene_builder.py        # Core logic, merging & validation
    ├── config_loader.py        # YAML & TOML parser
    ├── prompt_library.py       # Tag indexer
    └── exporter.py             # Dataset file generator

# Quick Start

## Installation

git clone https://github.com/your-username/dataset-composer.git
cd dataset-composer
python -m venv .venv
# Activate virtual environment
pip install pyyaml toml

## Test Mode (Generate 5 random scenes in console)

cd src
python main.py

## Generate Mode (Create a massive dataset)

python main.py generate [number of generated files]

This will create a dataset/ folder containing 1,000 perfectly formatted .txt files, ready to be paired with your generated images for LoRA training.