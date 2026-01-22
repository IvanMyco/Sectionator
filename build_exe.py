"""
Build Script per creare BXS Manager EXE
Esegui questo file per creare l'eseguibile Windows
"""
import os
import sys
import subprocess

# Cambia directory alla cartella dello script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

print("="*60)
print("BXS MANAGER - BUILD SCRIPT")
print("="*60)
print(f"\nCartella di lavoro: {SCRIPT_DIR}\n")

# Verifica Python 32-bit
import struct
bits = struct.calcsize('P') * 8
print(f"\n1. Verifica Python: {bits}-bit")
if bits != 32:
    print("   ❌ ERRORE: Devi usare Python 32-bit!")
    print("   Scarica Python 32-bit da: https://www.python.org/downloads/")
    sys.exit(1)
else:
    print("   ✓ Python 32-bit OK")

# Verifica PyInstaller installato
print("\n2. Verifica PyInstaller...")
try:
    import PyInstaller
    print(f"   ✓ PyInstaller {PyInstaller.__version__} installato")
except ImportError:
    print("   ❌ PyInstaller non installato!")
    print("   Installazione in corso...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("   ✓ PyInstaller installato")

# Verifica CustomTkinter
print("\n3. Verifica CustomTkinter...")
try:
    import customtkinter
    print(f"   ✓ CustomTkinter installato")
except ImportError:
    print("   ❌ CustomTkinter non installato!")
    print("   Installazione in corso...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    print("   ✓ CustomTkinter installato")

# Verifica file richiesti
print("\n4. Verifica file richiesti...")
required_files = [
    "bxs_generator_ui.py",
    "bxs_generator.py",
    "bxs_property_assigner.py",
    "beam_property_id_assigner.py",
    "strand7_config.py",
    "St7API.py"
]

missing = []
for f in required_files:
    if os.path.exists(f):
        print(f"   ✓ {f}")
    else:
        print(f"   ❌ {f} MANCANTE!")
        missing.append(f)

if missing:
    print(f"\n❌ File mancanti: {', '.join(missing)}")
    sys.exit(1)

# Build con PyInstaller
print("\n5. Creazione EXE...")
print("   Questo può richiedere qualche minuto...\n")

cmd = [
    "pyinstaller",
    "--onefile",                    # Un singolo file .exe
    "--windowed",                   # Senza console
    "--name=BXS_Manager",           # Nome dell'exe
    "--add-data", "St7API.py;.",    # Include St7API.py
    "--hidden-import=customtkinter", # Forza inclusione customtkinter
    "--collect-submodules", "customtkinter", # Include tutti i submoduli
    "bxs_generator_ui.py"           # File principale
]

try:
    subprocess.check_call(cmd)
    print("\n" + "="*60)
    print("✅ BUILD COMPLETATO CON SUCCESSO!")
    print("="*60)
    print("\nL'eseguibile si trova in:")
    print("   dist/BXS_Manager.exe")
    print("\nPer distribuire, copia:")
    print("   - dist/BXS_Manager.exe")
    print("   - [Opzionale] Cartella Strand7/ con St7api.dll")
    print("="*60)
except subprocess.CalledProcessError as e:
    print("\n❌ ERRORE durante il build!")
    print(f"   {e}")
    sys.exit(1)