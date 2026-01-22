"""
Strand7 DLL Configuration
Gestisce automaticamente il path della DLL Strand7
"""
import os
import sys

def get_strand7_dll_path():
    """
    Trova automaticamente la DLL Strand7 cercando in:
    1. Cartella locale (exe_dir/Strand7/St7api.dll)
    2. Installazione standard Strand7
    
    Returns:
        str: Path completo della DLL
        
    Raises:
        FileNotFoundError: Se la DLL non viene trovata
    """
    # Determina la directory base (funziona sia per .py che per .exe)
    if getattr(sys, 'frozen', False):
        # Eseguibile PyInstaller
        base_dir = os.path.dirname(sys.executable)
    else:
        # Script Python
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Prova nella sottocartella "Strand7" locale
    local_dll = os.path.join(base_dir, "Strand7", "St7api.dll")
    if os.path.exists(local_dll):
        print(f"✓ DLL Strand7 trovata (locale): {local_dll}")
        return local_dll
    
    # 2. Prova nell'installazione standard Strand7
    default_dll = r"C:\Program Files (x86)\Strand7 R24\Bin\St7api.dll"
    if os.path.exists(default_dll):
        print(f"✓ DLL Strand7 trovata (installazione): {default_dll}")
        return default_dll
    
    # 3. Non trovata
    error_msg = (
        "DLL Strand7 (St7api.dll) non trovata!\n"
        f"Cercata in:\n"
        f"  - {local_dll}\n"
        f"  - {default_dll}\n\n"
        "Assicurati che Strand7 R24 sia installato o copia St7api.dll "
        "nella sottocartella 'Strand7'."
    )
    raise FileNotFoundError(error_msg)

# Esporta il path della DLL
STRAND7_DLL_PATH = get_strand7_dll_path()
