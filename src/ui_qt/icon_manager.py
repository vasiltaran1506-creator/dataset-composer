# src/ui_qt/icon_manager.py
from PySide6.QtGui import QFontDatabase
from pathlib import Path
import urllib.request

class IconManager:
    _font_family = None
    _initialized = False
    
    # Material Design Icons (MDI v7.x) codepoints
    _codepoints = {
        # === Main Tabs ===
        'user': '\U000F0013', 'database': '\U000F01BC', 'rocket': '\U000F0467', 
        'chart': '\U000F0128', 'cog': '\U000F0493',
        
        # === Profiles Sub-Tabs ===
        'dna': '\U000F081F', 'tshirt': '\U000F0C4D', 'mask': '\U000F0690', 
        'star': '\U000F04CE', 'cloud': '\U000F015F', 'code': '\U000F0174', 'eye': '\U000F0208',
        
        # === Library Sub-Tabs ===
        'tag': '\U000F04F9', 'movie': '\U000F03A4',
        
        # === Main Actions ===
        'save': '\U000F0193', 'delete': '\U000F01B4', 'add': '\U000F0415', 
        'import': '\U000F02F4', 'folder': '\U000F024B', 'refresh': '\U000F0450', 
        'copy': '\U000F018F', 'search': '\U000F0349', 'dice': '\U000F01C2', 
        'check': '\U000F012C', 'info': '\U000F02FD', 'play': '\U000F040A', 
        'book': '\U000F0096', 'wand': '\U000F006F', 'edit': '\U000F03EB',
        
        # === Micro Actions (NEW) ===
        'plus': '\U000F0415',      # + (add)
        'minus': '\U000F0374',     # -
        'close': '\U000F0156',     # × (close/x)
        'help': '\U000F02D7',      # ? (help-circle)
        'chevron-right': '\U000F0142',  # ▶
        'chevron-down': '\U000F0140',   # ▼
        'star-outline': '\U000F04D2',   # ☆
        'pencil': '\U000F03EB',    # ✏
        'rename': '\U000F03EB',    # edit alias
        'download': '\U000F01DA',
        'upload': '\U000F0552',
        'filter': '\U000F0236',
        'link': '\U000F0339',
        'play-circle': '\U000F040A',
        'stop': '\U000F04DB',
        'clear': '\U000F0156',     # close alias
    }

    @classmethod
    def initialize(cls):
        if cls._initialized: return True
        assets_dir = Path(__file__).parent / "assets"
        assets_dir.mkdir(exist_ok=True)
        font_path = assets_dir / "materialdesignicons-webfont.ttf"
        
        if not font_path.exists():
            print(f"[IconManager] Font not found. Downloading MDI...")
            url = "https://github.com/Templarian/MaterialDesign-Webfont/raw/v7.4.47/fonts/materialdesignicons-webfont.ttf"
            try:
                urllib.request.urlretrieve(url, font_path)
                print("[IconManager] Download complete.")
            except Exception as e:
                print(f"[IconManager] Failed to download: {e}")
                cls._initialized = True
                return False
                
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id == -1:
            cls._initialized = True
            return False
            
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            cls._font_family = families[0]
            print(f"[IconManager] Loaded: {cls._font_family}")
            cls._initialized = True
            return True
        cls._initialized = True
        return False

    @classmethod
    def get(cls, name: str) -> str:
        """Возвращает Unicode-символ иконки."""
        if not cls._font_family: return ""
        return cls._codepoints.get(name, '')