"""
BXS Property Assigner
Assegna proprietà beam con sezioni BXS a un file Strand7 esistente
"""
import os
import sys
import ctypes
import glob
from typing import Callable, Optional, List, Tuple
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
# COSTANTI STRAND7
# ==============================================================================
# Beam Types
kBeamTypeNull = 0
kBeamTypeSpring = 1
kBeamTypeCable = 2
kBeamTypeTruss = 3
kBeamTypeCutOffBar = 4
kBeamTypePipe = 5
kBeamTypeBeam = 6
kBeamTypeConnection = 7
kBeamTypeContact = 8
kBeamTypeUser = 9

# Property Types
ptBEAMPROP = 1
ptPLATEPROP = 2
ptBRICKPROP = 3

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
# CLASSE PER ASSEGNAZIONE PROPRIETÀ BXS
# ==============================================================================
class BXSPropertyAssigner:
    """Gestisce l'assegnazione di proprietà beam con sezioni BXS"""
    
    def __init__(self, 
                 st7_file_path: str,
                 bxs_folder: str,
                 material_library_id: int = 16,
                 material_item_id: int = 2,
                 beam_type: int = kBeamTypeBeam,
                 property_name_prefix: str = "BXS_",
                 log_callback: Optional[Callable[[str], None]] = None):
        """
        Inizializza l'assegnatore di proprietà BXS
        
        Args:
            st7_file_path: Percorso completo del file .st7 di destinazione
            bxs_folder: Cartella contenente i file .bxs
            material_library_id: ID della libreria materiali (default: 16)
            material_item_id: ID dell'elemento materiale (default: 2)
            beam_type: Tipo di beam (default: kBeamTypeBeam)
            property_name_prefix: Prefisso per i nomi delle proprietà
            log_callback: Funzione callback per i log
        """
        self.st7_file_path = st7_file_path
        self.bxs_folder = bxs_folder
        self.material_library_id = material_library_id
        self.material_item_id = material_item_id
        self.beam_type = beam_type
        self.property_name_prefix = property_name_prefix
        self.log_callback = log_callback
        
        self.uID = 1
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
    
    def validate_inputs(self) -> bool:
        """Valida i file e cartelle di input"""
        # Verifica file .st7
        if not os.path.exists(self.st7_file_path):
            self.log(f"❌ ERRORE: File ST7 non trovato: {self.st7_file_path}")
            return False
        
        if not self.st7_file_path.lower().endswith('.st7'):
            self.log(f"❌ ERRORE: Il file deve avere estensione .st7")
            return False
        
        # Verifica cartella BXS
        if not os.path.exists(self.bxs_folder):
            self.log(f"❌ ERRORE: Cartella BXS non trovata: {self.bxs_folder}")
            return False
        
        return True
    
    def get_bxs_files(self) -> List[Tuple[str, str]]:
        """
        Trova tutti i file BXS nella cartella
        
        Returns:
            Lista di tuple (nome_base, percorso_completo)
        """
        pattern = os.path.join(self.bxs_folder, "*.bxs")
        files = glob.glob(pattern)
        
        bxs_list = []
        for file_path in sorted(files):
            basename = os.path.splitext(os.path.basename(file_path))[0]
            bxs_list.append((basename, file_path))
        
        self.log(f"📁 Trovati {len(bxs_list)} file(s) BXS")
        return bxs_list
    
    def get_total_beam_properties(self) -> Tuple[int, int]:
        """
        Ottiene il numero totale e il numero più alto di proprietà beam
        
        Returns:
            Tupla (totale_proprietà, proprietà_più_alta)
        """
        NumProperties = (ctypes.c_long * 4)()  # Array per i 4 tipi di proprietà
        LastProperty = (ctypes.c_long * 4)()   # Array per i numeri più alti
        
        ChkErr(St7API.St7GetTotalProperties(self.uID, NumProperties, LastProperty))
        
        total_beam_props = NumProperties[0]  # ipBeamPropTotal
        last_beam_prop = LastProperty[0]     # ipBeamPropTotal
        
        self.log(f"📊 Proprietà beam esistenti: {total_beam_props}")
        self.log(f"📊 Numero proprietà beam più alta: {last_beam_prop}")
        
        return total_beam_props, last_beam_prop
    
    def create_beam_property(self, prop_num: int, prop_name: str) -> bool:
        """
        Crea una nuova proprietà beam
        
        Args:
            prop_num: Numero della proprietà
            prop_name: Nome della proprietà
            
        Returns:
            True se successo
        """
        try:
            # Crea la proprietà
            ChkErr(St7API.St7NewBeamProperty(
                self.uID,
                prop_num,
                self.beam_type,
                prop_name.encode('cp1252')
            ))
            
            # Imposta esplicitamente il tipo beam
            ChkErr(St7API.St7SetBeamPropertyType(
                self.uID,
                prop_num,
                self.beam_type
            ))
            
            return True
        except Exception as e:
            self.log(f"❌ Errore creazione proprietà {prop_num}: {e}")
            return False
    
    def assign_material(self, prop_num: int) -> bool:
        """
        Assegna il materiale alla proprietà beam
        
        Args:
            prop_num: Numero della proprietà
            
        Returns:
            True se successo
        """
        try:
            ChkErr(St7API.St7AssignLibraryMaterial(
                self.uID,
                ptBEAMPROP,
                prop_num,
                self.material_library_id,
                self.material_item_id
            ))
            return True
        except Exception as e:
            self.log(f"❌ Errore assegnazione materiale: {e}")
            return False
    
    def assign_bxs(self, prop_num: int, bxs_path: str) -> bool:
        """
        Assegna la sezione BXS alla proprietà beam
        
        Args:
            prop_num: Numero della proprietà
            bxs_path: Percorso completo del file BXS
            
        Returns:
            True se successo
        """
        try:
            ChkErr(St7API.St7AssignBXS(
                self.uID,
                prop_num,
                bxs_path.encode('cp1252')
            ))
            return True
        except Exception as e:
            self.log(f"❌ Errore assegnazione BXS: {e}")
            return False
    
    def save_file(self) -> bool:
        """Salva il file Strand7"""
        try:
            ChkErr(St7API.St7SaveFile(self.uID))
            return True
        except Exception as e:
            self.log(f"❌ Errore salvataggio file: {e}")
            return False
    
    def process_single_bxs(self, prop_num: int, basename: str, bxs_path: str) -> bool:
        """
        Processa un singolo file BXS creando la proprietà associata
        
        Args:
            prop_num: Numero della proprietà da creare
            basename: Nome base del file BXS
            bxs_path: Percorso completo del file BXS
            
        Returns:
            True se successo
        """
        prop_name = f"{self.property_name_prefix}{basename}"
        
        try:
            self.log(f"\n{'─'*60}")
            self.log(f"📄 Elaborazione: {basename}")
            self.log(f"   Proprietà N°: {prop_num}")
            self.log(f"   Nome: {prop_name}")
            self.log(f"{'─'*60}")
            
            # 1. Crea nuova proprietà beam
            self.log("  [1/4] Creazione proprietà beam...")
            if not self.create_beam_property(prop_num, prop_name):
                return False
            
            if not self.save_file():
                return False
            
            # 2. Assegna materiale
            self.log(f"  [2/4] Assegnazione materiale (Lib:{self.material_library_id}, Item:{self.material_item_id})...")
            if not self.assign_material(prop_num):
                return False
            
            if not self.save_file():
                return False
            
            # 3. Assegna BXS
            self.log(f"  [3/4] Assegnazione sezione BXS...")
            if not self.assign_bxs(prop_num, bxs_path):
                return False
            
            if not self.save_file():
                return False
            
            # 4. Salvataggio finale
            self.log(f"  [4/4] Salvataggio completato")
            self.log(f"✅ COMPLETATO: Proprietà {prop_num} creata con successo!")
            
            return True
            
        except Exception as e:
            self.log(f"❌ ERRORE durante elaborazione di {basename}: {e}")
            return False
    
    def stop(self):
        """Ferma il processo"""
        self.should_stop = True
        self.log("⏸ Richiesta interruzione processo...")
    
    def run(self) -> dict:
        """
        Esegue il processo completo di assegnazione proprietà BXS
        
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
            self.log("🚀 AVVIO ASSEGNAZIONE PROPRIETÀ BXS")
            self.log("="*60)
            
            # Valida input
            if not self.validate_inputs():
                self.log("❌ Validazione input fallita. Processo interrotto.")
                return {"status": "validation_failed", **stats}
            
            # Inizializza API Strand7
            self.log("🔧 Inizializzazione Strand7 API...")
            ChkErr(St7API.St7Init())
            self.log("✓ API Strand7 inizializzata correttamente")
            
            # Apri file ST7
            self.log(f"📂 Apertura file: {os.path.basename(self.st7_file_path)}")
            ChkErr(St7API.St7OpenFile(self.uID, self.st7_file_path.encode('cp1252'), b""))
            self.log("✓ File ST7 aperto correttamente")
            
            # Ottieni proprietà beam esistenti
            total_props, last_prop = self.get_total_beam_properties()
            
            # Ottieni lista file BXS
            bxs_files = self.get_bxs_files()
            stats["total"] = len(bxs_files)
            
            if stats["total"] == 0:
                self.log("⚠ Nessun file BXS trovato nella cartella specificata")
                return {"status": "no_files", **stats}
            
            # Determina il numero di partenza per le nuove proprietà
            start_prop_num = last_prop + 1
            self.log(f"🔢 Numerazione proprietà: da {start_prop_num} a {start_prop_num + stats['total'] - 1}")
            
            # Processa ogni file BXS
            for idx, (basename, bxs_path) in enumerate(bxs_files, 1):
                if self.should_stop:
                    stats["skipped"] = stats["total"] - idx + 1
                    self.log(f"\n⏸ Processo interrotto dall'utente")
                    self.log(f"   File rimanenti non elaborati: {stats['skipped']}")
                    break
                
                prop_num = start_prop_num + idx - 1
                self.log(f"\n📊 Progresso: {idx}/{stats['total']}")
                
                if self.process_single_bxs(prop_num, basename, bxs_path):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            
            # Riepilogo finale
            self.log("\n" + "="*60)
            self.log("📊 RIEPILOGO FINALE")
            self.log("="*60)
            self.log(f"  Totale BXS:         {stats['total']}")
            self.log(f"  ✅ Successi:        {stats['success']}")
            self.log(f"  ❌ Falliti:         {stats['failed']}")
            if stats['skipped'] > 0:
                self.log(f"  ⏭ Saltati:          {stats['skipped']}")
            self.log(f"  📝 Proprietà create: da {start_prop_num} a {start_prop_num + stats['success'] - 1}")
            self.log("="*60)
            
            if stats['failed'] == 0 and stats['skipped'] == 0:
                self.log("🎉 Tutte le proprietà create con successo!")
                return {"status": "success", **stats}
            elif stats['success'] > 0:
                self.log("⚠ Processo completato con alcuni errori")
                return {"status": "partial_success", **stats}
            else:
                self.log("❌ Processo fallito")
                return {"status": "failed", **stats}
            
        except Exception as e:
            self.log(f"\n❌ ERRORE CRITICO: {e}")
            import traceback
            self.log(traceback.format_exc())
            return {"status": "error", "error": str(e), **stats}
        
        finally:
            # Chiudi file e rilascia API
            try:
                ChkErr(St7API.St7CloseFile(self.uID))
                self.log("📁 File ST7 chiuso")
            except:
                pass
            
            try:
                St7API.St7Release()
                self.log("🔌 API Strand7 rilasciata")
            except:
                pass
            
            self.is_running = False
            self.log("\n✓ Processo terminato\n")


# ==============================================================================
# ESEMPIO DI UTILIZZO
# ==============================================================================
if __name__ == "__main__":
    # Configurazione
    st7_file = r"C:\Users\rosso\Desktop\test_model.st7"
    bxs_folder = r"C:\Users\rosso\Desktop\BXS test\BXS_output"
    
    # Crea assegnatore
    assigner = BXSPropertyAssigner(
        st7_file_path=st7_file,
        bxs_folder=bxs_folder,
        material_library_id=16,
        material_item_id=2,
        beam_type=kBeamTypeBeam,
        property_name_prefix="BXS_"
    )
    
    # Esegui
    result = assigner.run()
    
    print(f"\nRisultato: {result}")
