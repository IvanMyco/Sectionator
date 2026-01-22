"""
BXS Generator - Interfaccia Utente
UI CustomTkinter per la generazione di file BXS da IGES e assegnazione proprietà
"""
import customtkinter as ctk
from tkinter import filedialog, StringVar
import threading
import os
from bxs_generator import BXSGenerator
from bxs_property_assigner import BXSPropertyAssigner, kBeamTypeBeam
from beam_property_id_assigner import BeamPropertyByIDAssigner

# ==============================================================================
# CONFIGURAZIONE CUSTOMTKINTER
# ==============================================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ==============================================================================
# CLASSE PRINCIPALE UI
# ==============================================================================
class BXSGeneratorUI:
    """Interfaccia grafica per BXS Generator"""
    
    def __init__(self):
        # Finestra principale
        self.root = ctk.CTk()
        self.root.title("BXS Manager - Strand7")
        self.root.geometry("950x750")
        self.root.minsize(850, 650)
        
        # Variabili TAB 1 - Generazione BXS
        self.iges_folder = StringVar(value=r"C:\Users\rosso\Desktop\BXS test")
        self.output_folder = StringVar(value=r"C:\Users\rosso\Desktop\BXS test\BXS_output")
        self.scratch_folder = StringVar(value=r"C:\Users\rosso\Desktop\Code\temp")
        
        # Variabili TAB 2 - Assegnazione Proprietà
        self.st7_file = StringVar(value=r"")
        self.bxs_input_folder = StringVar(value=r"C:\Users\rosso\Desktop\BXS test\BXS_output")
        self.property_prefix = StringVar(value="Sect_")
        
        # Variabili TAB 3 - Assegnazione Beam per ID
        self.st7_file_assign = StringVar(value=r"")
        self.beam_property_prefix = StringVar(value="sec_")
        
        self.generator = None
        self.assigner = None
        self.beam_assigner = None
        self.is_processing_gen = False
        self.is_processing_prop = False
        self.is_processing_beam = False
        
        # Configura layout responsivo
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Crea UI
        self.create_ui()
        
        # Gestione chiusura finestra
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_ui(self):
        """Crea tutti gli elementi dell'interfaccia"""
        
        # ==============================================================================
        # HEADER
        # ==============================================================================
        header_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color=("gray85", "gray20"))
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔧 BXS Manager - Strand7",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=15)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Generazione BXS da IGES e Assegnazione Proprietà Beam",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray70")
        )
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 15))
        
        # ==============================================================================
        # TABVIEW
        # ==============================================================================
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        
        # Crea le tre tab
        self.tabview.add("1️⃣ Generazione BXS")
        self.tabview.add("2️⃣ Creazione Proprietà")
        self.tabview.add("3️⃣ Assegnazione Beam")
        
        # Configura layout responsivo per le tab
        self.tabview.tab("1️⃣ Generazione BXS").grid_rowconfigure(1, weight=1)
        self.tabview.tab("1️⃣ Generazione BXS").grid_columnconfigure(0, weight=1)
        
        self.tabview.tab("2️⃣ Creazione Proprietà").grid_rowconfigure(1, weight=1)
        self.tabview.tab("2️⃣ Creazione Proprietà").grid_columnconfigure(0, weight=1)
        
        self.tabview.tab("3️⃣ Assegnazione Beam").grid_rowconfigure(1, weight=1)
        self.tabview.tab("3️⃣ Assegnazione Beam").grid_columnconfigure(0, weight=1)
        
        # Crea contenuti delle tab
        self.create_bxs_generation_tab()
        self.create_property_assignment_tab()
        self.create_beam_assignment_tab()
    
    # ==========================================================================
    # TAB 1: GENERAZIONE BXS
    # ==========================================================================
    def create_bxs_generation_tab(self):
        """Crea il contenuto della tab Generazione BXS"""
        tab = self.tabview.tab("1️⃣ Generazione BXS")
        
        # Configurazione Cartelle
        config_frame = ctk.CTkFrame(tab)
        config_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        config_frame.grid_columnconfigure(1, weight=1)
        
        config_title = ctk.CTkLabel(
            config_frame,
            text="📁 Configurazione Cartelle",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        config_title.grid(row=0, column=0, columnspan=3, padx=15, pady=(15, 10), sticky="w")
        
        self.create_folder_row(config_frame, 1, "Cartella IGES:", self.iges_folder, self.browse_iges)
        self.create_folder_row(config_frame, 2, "Cartella Output BXS:", self.output_folder, self.browse_output)
        self.create_folder_row(config_frame, 3, "Cartella Scratch:", self.scratch_folder, self.browse_scratch)
        
        # Log
        log_frame = ctk.CTkFrame(tab)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="📋 Log Elaborazione",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        self.log_textbox_gen = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.log_textbox_gen.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Controlli
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(10, 15))
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=1)
        
        self.start_button_gen = ctk.CTkButton(
            controls_frame,
            text="▶ AVVIA GENERAZIONE",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=("green", "#2d7a2d"),
            hover_color=("darkgreen", "#1f5a1f"),
            command=self.start_bxs_generation
        )
        self.start_button_gen.grid(row=0, column=0, padx=(15, 5), pady=10, sticky="ew")
        
        self.stop_button_gen = ctk.CTkButton(
            controls_frame,
            text="⏸ STOP",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=("orange", "#cc6600"),
            hover_color=("darkorange", "#995200"),
            command=self.stop_bxs_generation,
            state="disabled"
        )
        self.stop_button_gen.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        self.close_button_gen = ctk.CTkButton(
            controls_frame,
            text="✖ CHIUDI",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=("red", "#8b0000"),
            hover_color=("darkred", "#660000"),
            command=self.on_closing
        )
        self.close_button_gen.grid(row=0, column=2, padx=(5, 15), pady=10, sticky="ew")
        
        # Log iniziale
        self.log_gen("✓ Tab Generazione BXS caricata")
        self.log_gen("📌 Configura le cartelle e premi 'AVVIA GENERAZIONE'")
    
    # ==========================================================================
    # TAB 2: CREAZIONE PROPRIETÀ
    # ==========================================================================
    def create_property_assignment_tab(self):
        """Crea il contenuto della tab Creazione Proprietà"""
        tab = self.tabview.tab("2️⃣ Creazione Proprietà")
        
        # Configurazione
        config_frame = ctk.CTkFrame(tab)
        config_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        config_frame.grid_columnconfigure(1, weight=1)
        
        config_title = ctk.CTkLabel(
            config_frame,
            text="⚙️ Configurazione Proprietà",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        config_title.grid(row=0, column=0, columnspan=3, padx=15, pady=(15, 10), sticky="w")
        
        # File ST7 target
        self.create_file_row(config_frame, 1, "File ST7 Target:", self.st7_file, self.browse_st7_file)
        
        # Cartella BXS
        self.create_folder_row(config_frame, 2, "Cartella BXS:", self.bxs_input_folder, self.browse_bxs_folder)
        
        # Prefisso proprietà
        label_prefix = ctk.CTkLabel(
            config_frame,
            text="Prefisso Proprietà:",
            font=ctk.CTkFont(size=12),
            width=150,
            anchor="w"
        )
        label_prefix.grid(row=3, column=0, padx=(15, 10), pady=8, sticky="w")
        
        entry_prefix = ctk.CTkEntry(
            config_frame,
            textvariable=self.property_prefix,
            font=ctk.CTkFont(size=11),
            height=32,
            placeholder_text="Es: Sect_"
        )
        entry_prefix.grid(row=3, column=1, padx=(0, 10), pady=8, sticky="ew")
        
        info_label = ctk.CTkLabel(
            config_frame,
            text="ℹ️ Esempio: Sect_1, Sect_2, ...",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60")
        )
        info_label.grid(row=3, column=2, padx=(0, 15), pady=8, sticky="w")
        
        # Log
        log_frame = ctk.CTkFrame(tab)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="📋 Log Elaborazione",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        self.log_textbox_prop = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.log_textbox_prop.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Controlli
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(10, 15))
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=1)
        
        self.start_button_prop = ctk.CTkButton(
            controls_frame,
            text="▶ CREA PROPRIETÀ",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=("green", "#2d7a2d"),
            hover_color=("darkgreen", "#1f5a1f"),
            command=self.start_property_assignment
        )
        self.start_button_prop.grid(row=0, column=0, padx=(15, 5), pady=10, sticky="ew")
        
        self.stop_button_prop = ctk.CTkButton(
            controls_frame,
            text="⏸ STOP",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=("orange", "#cc6600"),
            hover_color=("darkorange", "#995200"),
            command=self.stop_property_assignment,
            state="disabled"
        )
        self.stop_button_prop.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        self.close_button_prop = ctk.CTkButton(
            controls_frame,
            text="✖ CHIUDI",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=("red", "#8b0000"),
            hover_color=("darkred", "#660000"),
            command=self.on_closing
        )
        self.close_button_prop.grid(row=0, column=2, padx=(5, 15), pady=10, sticky="ew")
        
        # Log iniziale
        self.log_prop("✓ Tab Creazione Proprietà caricata")
        self.log_prop("📌 Configura il file ST7, la cartella BXS e il prefisso")
    
    # ==========================================================================
    # TAB 3: ASSEGNAZIONE BEAM PER ID
    # ==========================================================================
    def create_beam_assignment_tab(self):
        """Crea il contenuto della tab Assegnazione Beam"""
        tab = self.tabview.tab("3️⃣ Assegnazione Beam")
        
        # Configurazione
        config_frame = ctk.CTkFrame(tab)
        config_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        config_frame.grid_columnconfigure(1, weight=1)
        
        config_title = ctk.CTkLabel(
            config_frame,
            text="🔗 Configurazione Assegnazione",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        config_title.grid(row=0, column=0, columnspan=3, padx=15, pady=(15, 10), sticky="w")
        
        # File ST7 target
        self.create_file_row(config_frame, 1, "File ST7:", self.st7_file_assign, self.browse_st7_file_assign)
        
        # Prefisso proprietà
        label_prefix = ctk.CTkLabel(
            config_frame,
            text="Prefisso Proprietà:",
            font=ctk.CTkFont(size=12),
            width=150,
            anchor="w"
        )
        label_prefix.grid(row=2, column=0, padx=(15, 10), pady=8, sticky="w")
        
        entry_prefix = ctk.CTkEntry(
            config_frame,
            textvariable=self.beam_property_prefix,
            font=ctk.CTkFont(size=11),
            height=32,
            placeholder_text="Es: sec_"
        )
        entry_prefix.grid(row=2, column=1, padx=(0, 10), pady=8, sticky="ew")
        
        info_label = ctk.CTkLabel(
            config_frame,
            text="ℹ️ Beam ID:411 → sec_411",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60")
        )
        info_label.grid(row=2, column=2, padx=(0, 15), pady=8, sticky="w")
        
        # Info box
        info_frame = ctk.CTkFrame(config_frame, fg_color=("gray90", "gray25"))
        info_frame.grid(row=3, column=0, columnspan=3, padx=15, pady=(10, 15), sticky="ew")
        
        info_text = ctk.CTkLabel(
            info_frame,
            text="📌 Questa funzione assegna le proprietà beam agli elementi beam\n"
                 "   in base al loro ID. Es: Beam con ID 411 riceve proprietà 'sec_411'",
            font=ctk.CTkFont(size=11),
            justify="left",
            text_color=("gray30", "gray80")
        )
        info_text.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # Log
        log_frame = ctk.CTkFrame(tab)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="📋 Log Elaborazione",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        self.log_textbox_beam = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.log_textbox_beam.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Controlli
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(10, 15))
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=1)
        
        self.start_button_beam = ctk.CTkButton(
            controls_frame,
            text="▶ ASSEGNA PROPRIETÀ",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=("green", "#2d7a2d"),
            hover_color=("darkgreen", "#1f5a1f"),
            command=self.start_beam_assignment
        )
        self.start_button_beam.grid(row=0, column=0, padx=(15, 5), pady=10, sticky="ew")
        
        self.stop_button_beam = ctk.CTkButton(
            controls_frame,
            text="⏸ STOP",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=("orange", "#cc6600"),
            hover_color=("darkorange", "#995200"),
            command=self.stop_beam_assignment,
            state="disabled"
        )
        self.stop_button_beam.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        self.close_button_beam = ctk.CTkButton(
            controls_frame,
            text="✖ CHIUDI",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=("red", "#8b0000"),
            hover_color=("darkred", "#660000"),
            command=self.on_closing
        )
        self.close_button_beam.grid(row=0, column=2, padx=(5, 15), pady=10, sticky="ew")
        
        # Log iniziale
        self.log_beam("✓ Tab Assegnazione Beam caricata")
        self.log_beam("📌 Seleziona file ST7 e configura il prefisso proprietà")
    
    def create_folder_row(self, parent, row, label, variable, browse_command):
        """Crea una riga per la selezione di una cartella"""
        label_widget = ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=12),
            width=150,
            anchor="w"
        )
        label_widget.grid(row=row, column=0, padx=(15, 10), pady=8, sticky="w")
        
        entry = ctk.CTkEntry(
            parent,
            textvariable=variable,
            font=ctk.CTkFont(size=11),
            height=32
        )
        entry.grid(row=row, column=1, padx=(0, 10), pady=8, sticky="ew")
        
        browse_btn = ctk.CTkButton(
            parent,
            text="📁 Sfoglia",
            width=100,
            height=32,
            command=browse_command
        )
        browse_btn.grid(row=row, column=2, padx=(0, 15), pady=8)
    
    def create_file_row(self, parent, row, label, variable, browse_command):
        """Crea una riga per la selezione di un file"""
        label_widget = ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=12),
            width=150,
            anchor="w"
        )
        label_widget.grid(row=row, column=0, padx=(15, 10), pady=8, sticky="w")
        
        entry = ctk.CTkEntry(
            parent,
            textvariable=variable,
            font=ctk.CTkFont(size=11),
            height=32
        )
        entry.grid(row=row, column=1, padx=(0, 10), pady=8, sticky="ew")
        
        browse_btn = ctk.CTkButton(
            parent,
            text="📄 Sfoglia",
            width=100,
            height=32,
            command=browse_command
        )
        browse_btn.grid(row=row, column=2, padx=(0, 15), pady=8)
    
    def browse_iges(self):
        """Seleziona cartella IGES"""
        folder = filedialog.askdirectory(
            title="Seleziona Cartella IGES",
            initialdir=self.iges_folder.get() if os.path.exists(self.iges_folder.get()) else None
        )
        if folder:
            self.iges_folder.set(folder)
            self.log_gen(f"📁 Cartella IGES impostata: {folder}")
    
    def browse_output(self):
        """Seleziona cartella output BXS"""
        folder = filedialog.askdirectory(
            title="Seleziona Cartella Output BXS",
            initialdir=self.output_folder.get() if os.path.exists(self.output_folder.get()) else None
        )
        if folder:
            self.output_folder.set(folder)
            self.log_gen(f"📁 Cartella Output impostata: {folder}")
    
    def browse_scratch(self):
        """Seleziona cartella scratch"""
        folder = filedialog.askdirectory(
            title="Seleziona Cartella Scratch",
            initialdir=self.scratch_folder.get() if os.path.exists(self.scratch_folder.get()) else None
        )
        if folder:
            self.scratch_folder.set(folder)
            self.log_gen(f"📁 Cartella Scratch impostata: {folder}")
    
    def browse_st7_file(self):
        """Seleziona file ST7 target"""
        file = filedialog.askopenfilename(
            title="Seleziona File ST7",
            initialdir=os.path.dirname(self.st7_file.get()) if self.st7_file.get() and os.path.exists(os.path.dirname(self.st7_file.get())) else None,
            filetypes=[("Strand7 Files", "*.st7"), ("All Files", "*.*")]
        )
        if file:
            self.st7_file.set(file)
            self.log_prop(f"📄 File ST7 impostato: {file}")
    
    def browse_bxs_folder(self):
        """Seleziona cartella BXS per proprietà"""
        folder = filedialog.askdirectory(
            title="Seleziona Cartella BXS",
            initialdir=self.bxs_input_folder.get() if os.path.exists(self.bxs_input_folder.get()) else None
        )
        if folder:
            self.bxs_input_folder.set(folder)
            self.log_prop(f"📁 Cartella BXS impostata: {folder}")
    
    def browse_st7_file_assign(self):
        """Seleziona file ST7 per assegnazione beam"""
        file = filedialog.askopenfilename(
            title="Seleziona File ST7",
            initialdir=os.path.dirname(self.st7_file_assign.get()) if self.st7_file_assign.get() and os.path.exists(os.path.dirname(self.st7_file_assign.get())) else None,
            filetypes=[("Strand7 Files", "*.st7"), ("All Files", "*.*")]
        )
        if file:
            self.st7_file_assign.set(file)
            self.log_beam(f"📄 File ST7 impostato: {file}")
    
    def log_gen(self, message):
        """Aggiunge un messaggio al log della tab Generazione BXS"""
        self.log_textbox_gen.configure(state="normal")
        self.log_textbox_gen.insert("end", message + "\n")
        self.log_textbox_gen.see("end")
        self.log_textbox_gen.configure(state="disabled")
        self.root.update_idletasks()
    
    def log_prop(self, message):
        """Aggiunge un messaggio al log della tab Assegnazione Proprietà"""
        self.log_textbox_prop.configure(state="normal")
        self.log_textbox_prop.insert("end", message + "\n")
        self.log_textbox_prop.see("end")
        self.log_textbox_prop.configure(state="disabled")
        self.root.update_idletasks()
    
    def log_beam(self, message):
        """Aggiunge un messaggio al log della tab Assegnazione Beam"""
        self.log_textbox_beam.configure(state="normal")
        self.log_textbox_beam.insert("end", message + "\n")
        self.log_textbox_beam.see("end")
        self.log_textbox_beam.configure(state="disabled")
        self.root.update_idletasks()
    
    def clear_log_gen(self):
        """Pulisce il log generazione"""
        self.log_textbox_gen.configure(state="normal")
        self.log_textbox_gen.delete("1.0", "end")
        self.log_textbox_gen.configure(state="disabled")
    
    def clear_log_prop(self):
        """Pulisce il log proprietà"""
        self.log_textbox_prop.configure(state="normal")
        self.log_textbox_prop.delete("1.0", "end")
        self.log_textbox_prop.configure(state="disabled")
    
    def clear_log_beam(self):
        """Pulisce il log beam"""
        self.log_textbox_beam.configure(state="normal")
        self.log_textbox_beam.delete("1.0", "end")
        self.log_textbox_beam.configure(state="disabled")
    
    def set_ui_state_gen(self, processing: bool):
        """Cambia lo stato dei pulsanti durante l'elaborazione BXS"""
        if processing:
            self.start_button_gen.configure(state="disabled")
            self.stop_button_gen.configure(state="normal")
            self.close_button_gen.configure(state="disabled")
        else:
            self.start_button_gen.configure(state="normal")
            self.stop_button_gen.configure(state="disabled")
            self.close_button_gen.configure(state="normal")
    
    def set_ui_state_prop(self, processing: bool):
        """Cambia lo stato dei pulsanti durante l'assegnazione proprietà"""
        if processing:
            self.start_button_prop.configure(state="disabled")
            self.stop_button_prop.configure(state="normal")
            self.close_button_prop.configure(state="disabled")
        else:
            self.start_button_prop.configure(state="normal")
            self.stop_button_prop.configure(state="disabled")
            self.close_button_prop.configure(state="normal")
    
    def set_ui_state_beam(self, processing: bool):
        """Cambia lo stato dei pulsanti durante l'assegnazione beam"""
        if processing:
            self.start_button_beam.configure(state="disabled")
            self.stop_button_beam.configure(state="normal")
            self.close_button_beam.configure(state="disabled")
        else:
            self.start_button_beam.configure(state="normal")
            self.stop_button_beam.configure(state="disabled")
            self.close_button_beam.configure(state="normal")
    
    # ==========================================================================
    # METODI GENERAZIONE BXS
    # ==========================================================================
    def start_bxs_generation(self):
        """Avvia il processo di generazione BXS in un thread separato"""
        if self.is_processing_gen:
            self.log_gen("⚠ Elaborazione già in corso!")
            return
        
        self.generator = BXSGenerator(
            iges_folder=self.iges_folder.get(),
            output_folder=self.output_folder.get(),
            scratch_folder=self.scratch_folder.get(),
            log_callback=self.log_gen
        )
        
        self.is_processing_gen = True
        self.set_ui_state_gen(processing=True)
        
        thread = threading.Thread(target=self._run_bxs_generator, daemon=True)
        thread.start()
    
    def _run_bxs_generator(self):
        """Esegue il generatore BXS (chiamato dal thread)"""
        try:
            result = self.generator.run()
        except Exception as e:
            self.log_gen(f"❌ Errore critico: {e}")
        finally:
            self.is_processing_gen = False
            self.root.after(0, lambda: self.set_ui_state_gen(processing=False))
    
    def stop_bxs_generation(self):
        """Ferma il processo di generazione BXS"""
        if self.generator and self.is_processing_gen:
            self.generator.stop()
    
    # ==========================================================================
    # METODI ASSEGNAZIONE PROPRIETÀ
    # ==========================================================================
    def start_property_assignment(self):
        """Avvia il processo di assegnazione proprietà in un thread separato"""
        if self.is_processing_prop:
            self.log_prop("⚠ Elaborazione già in corso!")
            return
        
        # Validazione input
        if not self.st7_file.get():
            self.log_prop("❌ ERRORE: Seleziona un file ST7!")
            return
        
        if not self.bxs_input_folder.get():
            self.log_prop("❌ ERRORE: Seleziona la cartella BXS!")
            return
        
        if not self.property_prefix.get():
            self.log_prop("❌ ERRORE: Inserisci un prefisso per le proprietà!")
            return
        
        self.assigner = BXSPropertyAssigner(
            st7_file_path=self.st7_file.get(),
            bxs_folder=self.bxs_input_folder.get(),
            material_library_id=16,
            material_item_id=2,
            beam_type=kBeamTypeBeam,
            property_name_prefix=self.property_prefix.get(),
            log_callback=self.log_prop
        )
        
        self.is_processing_prop = True
        self.set_ui_state_prop(processing=True)
        
        thread = threading.Thread(target=self._run_property_assigner, daemon=True)
        thread.start()
    
    def _run_property_assigner(self):
        """Esegue l'assegnatore proprietà (chiamato dal thread)"""
        try:
            result = self.assigner.run()
        except Exception as e:
            self.log_prop(f"❌ Errore critico: {e}")
        finally:
            self.is_processing_prop = False
            self.root.after(0, lambda: self.set_ui_state_prop(processing=False))
    
    def stop_property_assignment(self):
        """Ferma il processo di assegnazione proprietà"""
        if self.assigner and self.is_processing_prop:
            self.assigner.stop()
    
    # ==========================================================================
    # METODI ASSEGNAZIONE BEAM PER ID
    # ==========================================================================
    def start_beam_assignment(self):
        """Avvia il processo di assegnazione beam per ID in un thread separato"""
        if self.is_processing_beam:
            self.log_beam("⚠ Elaborazione già in corso!")
            return
        
        # Validazione input
        if not self.st7_file_assign.get():
            self.log_beam("❌ ERRORE: Seleziona un file ST7!")
            return
        
        if not self.beam_property_prefix.get():
            self.log_beam("❌ ERRORE: Inserisci un prefisso per le proprietà!")
            return
        
        self.beam_assigner = BeamPropertyByIDAssigner(
            st7_file_path=self.st7_file_assign.get(),
            property_prefix=self.beam_property_prefix.get(),
            log_callback=self.log_beam
        )
        
        self.is_processing_beam = True
        self.set_ui_state_beam(processing=True)
        
        thread = threading.Thread(target=self._run_beam_assigner, daemon=True)
        thread.start()
    
    def _run_beam_assigner(self):
        """Esegue l'assegnatore beam (chiamato dal thread)"""
        try:
            result = self.beam_assigner.run()
        except Exception as e:
            self.log_beam(f"❌ Errore critico: {e}")
        finally:
            self.is_processing_beam = False
            self.root.after(0, lambda: self.set_ui_state_beam(processing=False))
    
    def stop_beam_assignment(self):
        """Ferma il processo di assegnazione beam"""
        if self.beam_assigner and self.is_processing_beam:
            self.beam_assigner.stop()
    
    def on_closing(self):
        """Gestisce la chiusura della finestra"""
        if self.is_processing_gen or self.is_processing_prop or self.is_processing_beam:
            if self.is_processing_gen:
                self.log_gen("⚠ Elaborazione in corso. Arresto del processo...")
                self.stop_bxs_generation()
            if self.is_processing_prop:
                self.log_prop("⚠ Elaborazione in corso. Arresto del processo...")
                self.stop_property_assignment()
            if self.is_processing_beam:
                self.log_beam("⚠ Elaborazione in corso. Arresto del processo...")
                self.stop_beam_assignment()
            self.root.after(500, self._force_close)
        else:
            self.root.destroy()
    
    def _force_close(self):
        """Forza la chiusura dopo un breve ritardo"""
        self.root.destroy()
    
    def run(self):
        """Avvia l'applicazione"""
        self.root.mainloop()

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    try:
        app = BXSGeneratorUI()
        app.run()
    except Exception as e:
        print(f"Errore critico nell'avvio dell'applicazione: {e}")
        import traceback
        traceback.print_exc()