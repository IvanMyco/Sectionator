"""
BXS Generator - Modulo Core
Gestisce la logica di generazione file BXS da IGES usando Strand7 API
"""
import os
import sys
import ctypes
import glob
from typing import Callable, Optional
from datetime import datetime

# ==============================================================================
# CONFIGURAZIONE STRAND7 API
# ==============================================================================
from strand7_config import STRAND7_DLL_PATH

dll_dir = os.path.dirname(STRAND7_DLL_PATH)

# Configura PATH
os.environ['PATH'] = dll_dir + os.pathsep + os.environ['PATH']
if hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(dll_dir)

# Importa St7API
try:
    import St7API
except Exception as e:
    raise ImportError(f"Errore durante l'importazione di St7API: {e}")

# ==============================================================================
# FUNZIONI DI SUPPORTO
# ==============================================================================
def ChkErr(ErrorCode):
    """Verifica errori API Strand7"""
    if ErrorCode != 0:
        err_buffer = ctypes.create_string_buffer(255)
        St7API.St7GetAPIErrorString(ErrorCode, err_buffer, 255)
        raise Exception(f"Errore Strand7 ({ErrorCode}): {err_buffer.value.decode('ascii')}")

# ==============================================================================
# CLASSE PRINCIPALE PER GENERAZIONE BXS
# ==============================================================================
class BXSGenerator:
    """Gestisce la generazione di file BXS da IGES usando Strand7 API"""
    
    def __init__(self, iges_folder: str, output_folder: str, scratch_folder: str, 
                 log_callback: Optional[Callable[[str], None]] = None):
        """
        Inizializza il generatore BXS
        
        Args:
            iges_folder: Cartella contenente i file IGES
            output_folder: Cartella di output per i file BXS
            scratch_folder: Cartella temporanea di lavoro
            log_callback: Funzione callback per i log (opzionale)
        """
        self.iges_folder = iges_folder
        self.output_folder = output_folder
        self.scratch_folder = scratch_folder
        self.log_callback = log_callback
        self.is_running = False
        self.should_stop = False
        
    def log(self, message: str):
        """Invia messaggio al log con timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        if self.log_callback:
            self.log_callback(formatted_message)
        else:
            print(formatted_message)
    
    def validate_folders(self) -> bool:
        """Valida le cartelle di input/output"""
        if not os.path.exists(self.iges_folder):
            self.log(f"❌ ERRORE: Cartella IGES non trovata: {self.iges_folder}")
            return False
        
        # Crea cartelle output e scratch se non esistono
        try:
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
                self.log(f"✓ Cartella output creata: {self.output_folder}")
            
            if not os.path.exists(self.scratch_folder):
                os.makedirs(self.scratch_folder)
                self.log(f"✓ Cartella scratch creata: {self.scratch_folder}")
            
            return True
        except Exception as e:
            self.log(f"❌ ERRORE nella creazione delle cartelle: {e}")
            return False
    
    def get_iges_files(self) -> list:
        """Trova tutti i file IGES nella cartella di input"""
        pattern = os.path.join(self.iges_folder, "*.igs")
        files = glob.glob(pattern)
        self.log(f"📁 Trovati {len(files)} file(s) IGES")
        return files
    
    def stop(self):
        """Ferma il processo di generazione"""
        self.should_stop = True
        self.log("⏸ Richiesta interruzione processo...")
    
    def process_single_file(self, iges_path: str, uID: int = 1) -> bool:
        """
        Processa un singolo file IGES
        
        Args:
            iges_path: Percorso completo del file IGES
            uID: User ID per Strand7
            
        Returns:
            True se successo, False altrimenti
        """
        basename = os.path.splitext(os.path.basename(iges_path))[0]
        st7_temp = os.path.join(self.scratch_folder, f"temp_{basename}.st7")
        bxs_output = os.path.join(self.output_folder, f"{basename}.bxs")
        
        # Rimuovi file temporanei precedenti se esistono
        if os.path.exists(st7_temp):
            try:
                os.remove(st7_temp)
                self.log(f"  🗑️ File temporaneo precedente rimosso")
            except:
                pass
        
        try:
            self.log(f"\n{'='*60}")
            self.log(f"📄 Elaborazione: {basename}")
            self.log(f"{'='*60}")
            
            # 1. New File
            self.log("  [1/6] Creazione nuovo file Strand7...")
            ChkErr(St7API.St7NewFile(uID, st7_temp.encode('ascii'), 
                                     self.scratch_folder.encode('ascii')))
            
            # 2. Import IGES
            self.log("  [2/6] Importazione IGES...")
            opts = (ctypes.c_long * 6)(0, 0, 1, 1, 0, 2)
            d_opts = (ctypes.c_double * 1)(0.0)
            ChkErr(St7API.St7ImportIGESFile(uID, iges_path.encode('ascii'), 
                                            opts, d_opts, 1))
            
            # 3. Surface Mesh
            self.log("  [3/6] Generazione mesh superficiale...")
            m_sel = (ctypes.c_long * 9)(1, 0, 4, -1, 1, 12, 1, 1, 1)
            m_siz = (ctypes.c_double * 4)(0.5, 0.1, 30.0, 0.0)
            ChkErr(St7API.St7SurfaceMesh(uID, m_sel, m_siz, 1))
            
            # 4. Clean Mesh
            self.log("  [4/6] Pulizia mesh...")
            clean = (ctypes.c_long * 15)(0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0)
            tol = ctypes.c_double(0.0001)
            ChkErr(St7API.St7SetCleanMeshData(uID, clean, ctypes.byref(tol)))
            ChkErr(St7API.St7CleanMesh(uID))
            
            # 5. Generate BXS
            self.log("  [5/6] Generazione file BXS...")
            prop_bxs = (ctypes.c_double * 34)()
            ChkErr(St7API.St7GenerateBXS(uID, bxs_output.encode('ascii'), prop_bxs))
            
            # 6. Salva e Chiudi
            self.log("  [6/6] Salvataggio e chiusura...")
            ChkErr(St7API.St7SaveFile(uID))
            ChkErr(St7API.St7CloseFile(uID))
            
            self.log(f"✅ COMPLETATO: {basename}.bxs creato con successo!")
            return True
            
        except Exception as e:
            self.log(f"❌ ERRORE durante elaborazione di {basename}: {e}")
            try:
                # Tenta di chiudere il file in caso di errore
                St7API.St7CloseFile(uID)
            except:
                pass
            return False
    
    def run(self) -> dict:
        """
        Esegue il processo completo di generazione BXS
        
        Returns:
            dict con statistiche di elaborazione
        """
        if self.is_running:
            self.log("⚠ Processo già in esecuzione!")
            return {"status": "already_running"}
        
        self.is_running = True
        self.should_stop = False
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        try:
            self.log("\n" + "="*60)
            self.log("🚀 AVVIO GENERAZIONE BXS")
            self.log("="*60)
            
            # Valida cartelle
            if not self.validate_folders():
                self.log("❌ Validazione cartelle fallita. Processo interrotto.")
                return {"status": "validation_failed", **stats}
            
            # Inizializza API Strand7
            self.log("🔧 Inizializzazione Strand7 API...")
            ChkErr(St7API.St7Init())
            self.log("✓ API Strand7 inizializzata correttamente")
            
            # Ottieni lista file IGES
            iges_files = self.get_iges_files()
            stats["total"] = len(iges_files)
            
            if stats["total"] == 0:
                self.log("⚠ Nessun file IGES trovato nella cartella specificata")
                return {"status": "no_files", **stats}
            
            # Processa ogni file
            for idx, iges_path in enumerate(iges_files, 1):
                if self.should_stop:
                    stats["skipped"] = stats["total"] - idx + 1
                    self.log(f"\n⏸ Processo interrotto dall'utente")
                    self.log(f"   File rimanenti non elaborati: {stats['skipped']}")
                    break
                
                self.log(f"\n📊 Progresso: {idx}/{stats['total']}")
                
                if self.process_single_file(iges_path):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            
            # Riepilogo finale
            self.log("\n" + "="*60)
            self.log("📊 RIEPILOGO FINALE")
            self.log("="*60)
            self.log(f"  Totale file:        {stats['total']}")
            self.log(f"  ✅ Successi:        {stats['success']}")
            self.log(f"  ❌ Falliti:         {stats['failed']}")
            if stats['skipped'] > 0:
                self.log(f"  ⏭ Saltati:          {stats['skipped']}")
            self.log("="*60)
            
            if stats['failed'] == 0 and stats['skipped'] == 0:
                self.log("🎉 Tutti i file elaborati con successo!")
                return {"status": "success", **stats}
            elif stats['success'] > 0:
                self.log("⚠ Processo completato con alcuni errori")
                return {"status": "partial_success", **stats}
            else:
                self.log("❌ Processo fallito")
                return {"status": "failed", **stats}
            
        except Exception as e:
            self.log(f"\n❌ ERRORE CRITICO: {e}")
            return {"status": "error", "error": str(e), **stats}
        
        finally:
            # Rilascia API Strand7
            try:
                St7API.St7Release()
                self.log("🔌 API Strand7 rilasciata")
            except:
                pass
            
            self.is_running = False
            self.log("\n✓ Processo terminato\n")
