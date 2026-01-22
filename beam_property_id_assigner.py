"""
Beam Property Assignment by ID
Assegna proprietà beam agli elementi beam in base al loro ID
"""
import os
import sys
import ctypes
from typing import Callable, Optional, Dict
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
# Entity Types
tyBEAM = 1
tyPLATE = 2
tyBRICK = 3

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
# CLASSE PER ASSEGNAZIONE PROPRIETÀ PER ID
# ==============================================================================
class BeamPropertyByIDAssigner:
    """Assegna proprietà beam agli elementi in base al loro ID"""
    
    def __init__(self, 
                 st7_file_path: str,
                 property_prefix: str = "sec_",
                 log_callback: Optional[Callable[[str], None]] = None):
        """
        Inizializza l'assegnatore
        
        Args:
            st7_file_path: Percorso completo del file .st7
            property_prefix: Prefisso delle proprietà (default: "sec_")
            log_callback: Funzione callback per i log
        """
        self.st7_file_path = st7_file_path
        self.property_prefix = property_prefix.lower()  # Normalizza in minuscolo
        self.log_callback = log_callback
        
        self.uID = 1
        self.is_running = False
        self.should_stop = False
        
        # Dizionari di lavoro
        self.property_map = {}  # {nome_proprietà: PropNum}
        self.beam_assignments = {}  # {beam_num: (beam_id, prop_num)}
    
    def log(self, message: str):
        """Invia messaggio al log con timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        if self.log_callback:
            self.log_callback(formatted_message)
        else:
            print(formatted_message)
    
    def validate_inputs(self) -> bool:
        """Valida il file di input"""
        if not os.path.exists(self.st7_file_path):
            self.log(f"❌ ERRORE: File ST7 non trovato: {self.st7_file_path}")
            return False
        
        if not self.st7_file_path.lower().endswith('.st7'):
            self.log(f"❌ ERRORE: Il file deve avere estensione .st7")
            return False
        
        return True
    
    def build_property_map(self) -> bool:
        """
        Costruisce un dizionario nome_proprietà -> PropNum
        
        Returns:
            True se successo
        """
        try:
            # Ottieni numero totale di proprietà
            NumProperties = (ctypes.c_long * 4)()
            LastProperty = (ctypes.c_long * 4)()
            ChkErr(St7API.St7GetTotalProperties(self.uID, NumProperties, LastProperty))
            
            total_beam_props = NumProperties[0]  # ipBeamPropTotal
            last_beam_prop = LastProperty[0]     # ipBeamPropTotal
            
            self.log(f"📊 Proprietà beam totali: {total_beam_props}")
            self.log(f"📊 Numero proprietà più alta: {last_beam_prop}")
            
            if total_beam_props == 0:
                self.log("⚠ ATTENZIONE: Nessuna proprietà beam trovata nel modello!")
                return False
            
            # Scansiona tutte le proprietà beam
            self.log(f"🔍 Scansione proprietà beam (da 1 a {last_beam_prop})...")
            
            prop_name_buffer = ctypes.create_string_buffer(256)
            found_count = 0
            
            for prop_num in range(1, last_beam_prop + 1):
                try:
                    # Leggi il nome della proprietà
                    ChkErr(St7API.St7GetPropertyName(
                        self.uID,
                        ptBEAMPROP,
                        prop_num,
                        prop_name_buffer,
                        256
                    ))
                    
                    prop_name = prop_name_buffer.value.decode('cp1252').strip()
                    
                    # Normalizza in minuscolo per confronto case-insensitive
                    prop_name_lower = prop_name.lower()
                    
                    # Salva nel dizionario
                    self.property_map[prop_name_lower] = prop_num
                    found_count += 1
                    
                    # Log se inizia con il prefisso cercato
                    if prop_name_lower.startswith(self.property_prefix):
                        self.log(f"  ✓ Trovata: {prop_name} (PropNum: {prop_num})")
                
                except Exception as e:
                    # Proprietà non esistente, salta
                    continue
            
            self.log(f"✅ Mappa proprietà costruita: {found_count} proprietà trovate")
            
            # Conta quante iniziano con il prefisso
            prefix_count = sum(1 for name in self.property_map.keys() 
                             if name.startswith(self.property_prefix))
            self.log(f"📌 Proprietà con prefisso '{self.property_prefix}': {prefix_count}")
            
            return found_count > 0
            
        except Exception as e:
            self.log(f"❌ Errore durante costruzione mappa proprietà: {e}")
            return False
    
    def get_beam_count(self) -> int:
        """
        Ottiene il numero totale di beam nel modello
        
        Returns:
            Numero di beam
        """
        Total = ctypes.c_long()
        ChkErr(St7API.St7GetTotal(self.uID, tyBEAM, ctypes.byref(Total)))
        return Total.value
    
    def get_beam_id(self, beam_num: int) -> int:
        """
        Ottiene l'ID di una beam dato il suo numero
        
        Args:
            beam_num: Numero della beam (1-based)
            
        Returns:
            ID della beam
        """
        BeamID = ctypes.c_long()
        ChkErr(St7API.St7GetBeamID(self.uID, beam_num, ctypes.byref(BeamID)))
        return BeamID.value
    
    def find_property_for_beam_id(self, beam_id: int) -> Optional[int]:
        """
        Trova il PropNum della proprietà corrispondente all'ID della beam
        
        Args:
            beam_id: ID della beam
            
        Returns:
            PropNum se trovato, None altrimenti
        """
        # Costruisci il nome atteso (es: "sec_411")
        expected_name = f"{self.property_prefix}{beam_id}".lower()
        
        # Cerca nel dizionario
        return self.property_map.get(expected_name)
    
    def assign_property_to_beam(self, beam_num: int, prop_num: int) -> bool:
        """
        Assegna una proprietà a una beam
        
        Args:
            beam_num: Numero della beam
            prop_num: Numero della proprietà
            
        Returns:
            True se successo
        """
        try:
            ChkErr(St7API.St7SetElementProperty(
                self.uID,
                tyBEAM,
                beam_num,
                prop_num
            ))
            return True
        except Exception as e:
            self.log(f"❌ Errore assegnazione proprietà {prop_num} a beam {beam_num}: {e}")
            return False
    
    def save_file(self) -> bool:
        """Salva il file Strand7"""
        try:
            ChkErr(St7API.St7SaveFile(self.uID))
            return True
        except Exception as e:
            self.log(f"❌ Errore salvataggio file: {e}")
            return False
    
    def stop(self):
        """Ferma il processo"""
        self.should_stop = True
        self.log("⏸ Richiesta interruzione processo...")
    
    def run(self) -> dict:
        """
        Esegue il processo completo di assegnazione
        
        Returns:
            dict con statistiche
        """
        if self.is_running:
            self.log("⚠ Processo già in esecuzione!")
            return {"status": "already_running"}
        
        self.is_running = True
        self.should_stop = False
        
        stats = {
            "total_beams": 0,
            "assigned": 0,
            "not_found": 0,
            "skipped": 0,
            "failed": 0
        }
        
        try:
            self.log("\n" + "="*60)
            self.log("🚀 AVVIO ASSEGNAZIONE PROPRIETÀ PER ID")
            self.log("="*60)
            self.log(f"📌 Prefisso proprietà: '{self.property_prefix}'")
            
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
            
            # Costruisci mappa proprietà
            self.log("\n" + "─"*60)
            self.log("📖 FASE 1: Costruzione mappa proprietà")
            self.log("─"*60)
            if not self.build_property_map():
                self.log("❌ Impossibile costruire mappa proprietà. Processo interrotto.")
                return {"status": "property_map_failed", **stats}
            
            # Ottieni numero beam
            self.log("\n" + "─"*60)
            self.log("📖 FASE 2: Scansione beam e assegnazione")
            self.log("─"*60)
            total_beams = self.get_beam_count()
            stats["total_beams"] = total_beams
            self.log(f"📊 Beam totali nel modello: {total_beams}")
            
            if total_beams == 0:
                self.log("⚠ Nessuna beam trovata nel modello!")
                return {"status": "no_beams", **stats}
            
            # Scansiona e assegna
            for beam_num in range(1, total_beams + 1):
                if self.should_stop:
                    stats["skipped"] = total_beams - beam_num + 1
                    self.log(f"\n⏸ Processo interrotto dall'utente")
                    self.log(f"   Beam rimanenti: {stats['skipped']}")
                    break
                
                try:
                    # Ottieni ID beam
                    beam_id = self.get_beam_id(beam_num)
                    
                    # Trova proprietà corrispondente
                    prop_num = self.find_property_for_beam_id(beam_id)
                    
                    if prop_num is not None:
                        # Proprietà trovata, assegna
                        if self.assign_property_to_beam(beam_num, prop_num):
                            self.log(f"  ✅ Beam #{beam_num} (ID:{beam_id}) → Proprietà {prop_num} ({self.property_prefix}{beam_id})")
                            stats["assigned"] += 1
                            self.beam_assignments[beam_num] = (beam_id, prop_num)
                        else:
                            stats["failed"] += 1
                    else:
                        # Proprietà non trovata
                        self.log(f"  ⚠ Beam #{beam_num} (ID:{beam_id}) → Proprietà '{self.property_prefix}{beam_id}' NON TROVATA")
                        stats["not_found"] += 1
                
                except Exception as e:
                    self.log(f"  ❌ Errore beam #{beam_num}: {e}")
                    stats["failed"] += 1
            
            # Salva file
            self.log("\n" + "─"*60)
            self.log("💾 Salvataggio modifiche...")
            if self.save_file():
                self.log("✓ File salvato correttamente")
            else:
                self.log("⚠ Attenzione: errore durante salvataggio")
            
            # Riepilogo finale
            self.log("\n" + "="*60)
            self.log("📊 RIEPILOGO FINALE")
            self.log("="*60)
            self.log(f"  Beam totali:           {stats['total_beams']}")
            self.log(f"  ✅ Assegnate:          {stats['assigned']}")
            self.log(f"  ⚠ Non trovate:         {stats['not_found']}")
            self.log(f"  ❌ Errori:             {stats['failed']}")
            if stats['skipped'] > 0:
                self.log(f"  ⏭ Saltate:             {stats['skipped']}")
            
            success_rate = (stats['assigned'] / stats['total_beams'] * 100) if stats['total_beams'] > 0 else 0
            self.log(f"  📈 Tasso successo:     {success_rate:.1f}%")
            self.log("="*60)
            
            if stats['assigned'] == stats['total_beams']:
                self.log("🎉 Tutte le beam assegnate con successo!")
                return {"status": "success", **stats}
            elif stats['assigned'] > 0:
                self.log("⚠ Processo completato con alcune beam non assegnate")
                return {"status": "partial_success", **stats}
            else:
                self.log("❌ Nessuna beam assegnata")
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
    st7_file = r"C:\Users\rosso\Desktop\Code\inserire_proprietà.st7"
    property_prefix = "sec_"
    
    # Crea assegnatore
    assigner = BeamPropertyByIDAssigner(
        st7_file_path=st7_file,
        property_prefix=property_prefix
    )
    
    # Esegui
    result = assigner.run()
    
    print(f"\nRisultato: {result}")
