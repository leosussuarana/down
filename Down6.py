import os
import re
import sys
import math
import shutil
import zipfile
import subprocess
import threading
import time
import urllib.request
import urllib.parse
import webbrowser
import tkinter as tk
from tkinter import filedialog, ttk

#====================================================
# RESOLUÇÃO DO DIRETÓRIO BASE E LOCALIZAÇÃO DE RECURSOS
#====================================================
if getattr(sys, 'frozen', False):
    PASTA_APP = os.path.dirname(os.path.abspath(sys.executable))
    PASTA_BUNDLE = getattr(sys, '_MEIPASS', PASTA_APP)
else:
    PASTA_APP = os.path.dirname(os.path.abspath(sys.argv[0]))
    PASTA_BUNDLE = PASTA_APP

def obter_caminho_icone() -> str:
    locais = [
        os.path.join(PASTA_APP, "logo.ico"),
        os.path.join(PASTA_BUNDLE, "logo.ico"),
        os.path.join(os.getcwd(), "logo.ico")
    ]
    for caminho in locais:
        if os.path.exists(caminho):
            return caminho
    return ""

def obter_pasta_downloads_windows() -> str:
    user_profile = os.environ.get('USERPROFILE')
    if user_profile:
        pasta_dl = os.path.join(user_profile, "Downloads")
        if os.path.exists(pasta_dl):
            return pasta_dl
    return os.path.join(os.path.expanduser("~"), "Downloads")

#====================================================
# PALETA DE CORES DEFINITIVA
#====================================================
COR_FUNDO = "#0B132B"
COR_CONTAINER = "#1C2541"
COR_CARD_HOVER = "#243257"
COR_AMARELO = "#FFD700"
COR_AMARELO_HOVER = "#FFC300"
COR_BRANCO = "#FFFFFF"
COR_PRETO = "#030508"
COR_CINZA_TEXTO = "#94A3B8"
COR_PLACEHOLDER = "#64748B"
COR_VERDE_OK = "#10B981"
COR_VERMELHO = "#EF4444"
PLACEHOLDER_NOME = "Deixe em branco para usar o nome original"

#====================================================
# UTILITÁRIOS DE VERIFICAÇÃO DE DEPENDÊNCIAS
#====================================================
def checar_executavel(nome: str) -> bool:
    caminho_local = os.path.join(PASTA_APP, f"{nome}.exe" if os.name == 'nt' else nome)
    if os.path.exists(caminho_local):
        return True
    return shutil.which(nome) is not None

def obter_comando(nome: str) -> str:
    caminho_local = os.path.join(PASTA_APP, f"{nome}.exe" if os.name == 'nt' else nome)
    if os.path.exists(caminho_local):
        return caminho_local
    return nome

#====================================================
# CLASSE DE NOTIFICAÇÃO TOAST FLUTUANTE
#====================================================
class ToastNotification:
    @staticmethod
    def show(parent, titulo: str, mensagem: str):
        toast = tk.Toplevel(parent)
        toast.overrideredirect(True)
        toast.configure(bg=COR_CONTAINER)
        toast.attributes("-topmost", True)
        
        largura, altura = 360, 75
        parent.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() - largura - 25
        py = parent.winfo_y() + parent.winfo_height() - altura - 25
        toast.geometry(f"{largura}x{altura}+{px}+{py}")
        
        borda = tk.Frame(toast, bg=COR_AMARELO, width=5)
        borda.pack(side=tk.LEFT, fill=tk.Y)
        
        corpo = tk.Frame(toast, bg=COR_CONTAINER, padx=12, pady=8)
        corpo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        lbl_t = tk.Label(corpo, text=titulo, font=("Segoe UI", 10, "bold"), bg=COR_CONTAINER, fg=COR_AMARELO)
        lbl_t.pack(anchor="w")
        
        lbl_m = tk.Label(corpo, text=mensagem, font=("Segoe UI", 8), bg=COR_CONTAINER, fg=COR_BRANCO, wraplength=320, justify="left")
        lbl_m.pack(anchor="w", pady=(2, 0))
        
        toast.after(2000, toast.destroy)

#====================================================
# CAIXAS DE MENSAGEM NATIVAS DO APLICATIVO
#====================================================
class ModalMensagem:
    @staticmethod
    def show(parent, titulo: str, mensagem: str, tipo: str = "info"):
        win = tk.Toplevel(parent)
        win.title(titulo)
        win.geometry("480x240")
        win.configure(bg=COR_FUNDO)
        win.transient(parent)
        win.attributes("-topmost", True)
        win.grab_set()
        
        ico = obter_caminho_icone()
        if ico:
            try: win.iconbitmap(ico)
            except Exception: pass
            
        parent.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 240
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 120
        win.geometry(f"+{px}+{py}")
        
        corpo = tk.Frame(win, bg=COR_CONTAINER, bd=1, relief=tk.SOLID, padx=20, pady=20)
        corpo.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        cor_titulo = COR_VERMELHO if tipo == "erro" else (COR_AMARELO if tipo == "aviso" else COR_VERDE_OK)
        lbl_tit = tk.Label(corpo, text=titulo.upper(), font=("Segoe UI", 12, "bold"), bg=COR_CONTAINER, fg=cor_titulo)
        lbl_tit.pack(pady=(0, 10))
        
        lbl_msg = tk.Label(corpo, text=mensagem, font=("Segoe UI", 10), bg=COR_CONTAINER, fg=COR_BRANCO, wraplength=400, justify="center")
        lbl_msg.pack(expand=True, pady=(0, 15))
        
        btn_ok = tk.Button(corpo, text="OK", command=win.destroy, font=("Segoe UI", 9, "bold"), bg=COR_AMARELO, fg=COR_PRETO, relief=tk.FLAT, cursor="hand2", padx=30, pady=5)
        btn_ok.pack()
        win.wait_window()

    @staticmethod
    def ask_yes_no(parent, titulo: str, mensagem: str) -> bool:
        win = tk.Toplevel(parent)
        win.title(titulo)
        win.geometry("480x240")
        win.configure(bg=COR_FUNDO)
        win.transient(parent)
        win.attributes("-topmost", True)
        win.grab_set()
        
        ico = obter_caminho_icone()
        if ico:
            try: win.iconbitmap(ico)
            except Exception: pass
            
        parent.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 240
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 120
        win.geometry(f"+{px}+{py}")
        
        corpo = tk.Frame(win, bg=COR_CONTAINER, bd=1, relief=tk.SOLID, padx=20, pady=20)
        corpo.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        lbl_tit = tk.Label(corpo, text=titulo.upper(), font=("Segoe UI", 12, "bold"), bg=COR_CONTAINER, fg=COR_AMARELO)
        lbl_tit.pack(pady=(0, 10))
        
        lbl_msg = tk.Label(corpo, text=mensagem, font=("Segoe UI", 10), bg=COR_CONTAINER, fg=COR_BRANCO, wraplength=400, justify="center")
        lbl_msg.pack(expand=True, pady=(0, 15))
        
        frame_btn = tk.Frame(corpo, bg=COR_CONTAINER)
        frame_btn.pack()
        
        resultado = tk.BooleanVar(value=False)
        
        def set_yes():
            resultado.set(True)
            win.destroy()
            
        def set_no():
            resultado.set(False)
            win.destroy()
            
        btn_yes = tk.Button(frame_btn, text="SIM", command=set_yes, font=("Segoe UI", 9, "bold"), bg=COR_AMARELO, fg=COR_PRETO, relief=tk.FLAT, cursor="hand2", padx=25, pady=5)
        btn_yes.pack(side=tk.LEFT, padx=10)
        
        btn_no = tk.Button(frame_btn, text="NÃO", command=set_no, font=("Segoe UI", 9, "bold"), bg=COR_PRETO, fg=COR_BRANCO, relief=tk.FLAT, cursor="hand2", padx=25, pady=5)
        btn_no.pack(side=tk.LEFT, padx=10)
        
        win.wait_window()
        return resultado.get()

#====================================================
# MODAL: COMO USAR
#====================================================
class ModalComoUsar:
    @staticmethod
    def abrir(parent):
        janela = tk.Toplevel(parent)
        janela.title("Guia do Usuário - Como Capturar Links & Baixar")
        janela.geometry("760x650")
        janela.minsize(700, 580)
        janela.configure(bg=COR_FUNDO)
        janela.transient(parent)
        janela.grab_set()
        
        ico = obter_caminho_icone()
        if ico:
            try: janela.iconbitmap(ico)
            except Exception: pass
                
        parent.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 380
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 325
        janela.geometry(f"+{px}+{py}")
        
        corpo = tk.Frame(janela, bg=COR_CONTAINER, bd=1, relief=tk.SOLID, padx=20, pady=20)
        corpo.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        lbl_tit = tk.Label(corpo, text="GUIA RÁPIDO DE OPERAÇÃO", font=("Segoe UI", 15, "bold"), bg=COR_CONTAINER, fg=COR_AMARELO)
        lbl_tit.pack(anchor="w")
        
        lbl_sub = tk.Label(corpo, text="Aprenda a obter o link de qualquer vídeo e a operar o DOWN 6.1e.", font=("Segoe UI", 9), bg=COR_CONTAINER, fg=COR_CINZA_TEXTO)
        lbl_sub.pack(anchor="w", pady=(2, 10))
        
        frame_txt = tk.Frame(corpo, bg=COR_PRETO, bd=1, relief=tk.SOLID)
        frame_txt.pack(fill=tk.BOTH, expand=True, pady=(5, 12))
        
        txt = tk.Text(frame_txt, bg=COR_PRETO, fg=COR_BRANCO, font=("Segoe UI", 9), relief=tk.FLAT, wrap=tk.WORD, padx=10, pady=10)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sb = tk.Scrollbar(frame_txt, command=txt.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.config(yscrollcommand=sb.set)
        
        tutorial = (
            "PASSO 1: LINKS DO YOUTUBE E PLATAFORMAS ABERTAS\n"
            "Para vídeos do YouTube:\n"
            "Basta copiar a URL normal da barra de endereços do navegador (ex: https://www.youtube.com/watch?v=...) ou o link "
            "de compartilhamento (youtu.be) e colar diretamente no campo de link do DOWN 6.1e. O download ocorrerá na maior resolução disponível.\n\n"
            "PASSO 2: COMO PEGAR O LINK DO VÍDEO NA HOTMART E CURSOS PROTEGIDOS\n"
            "1. Abra a página da aula no seu navegador (Google Chrome, Edge, Brave ou Firefox).\n"
            "2. Pressione a tecla F12 (ou clique com o botão direito e selecione 'Inspecionar').\n"
            "3. Na janela do desenvolvedor, clique na aba 'Rede' (Network).\n"
            "4. No campo de busca/filtro, digite: m3u8 (se não aparecer, digite: mp4).\n"
            "5. Dê PLAY no vídeo da aula.\n"
            "6. Clique com o BOTÃO DIREITO na linha do manifesto (ex: 'master-pkg...') > Copiar > 'Copiar endereço do link'.\n"
            "7. Cole o link no DOWN 6.1e.\n\n"
            "PASSO 3: MODO VÍDEO OU ÁUDIO\n"
            "No topo do aplicativo, você encontra as chaves de formato:\n"
            "[ VÍDEO: ON ] -> O aplicativo baixa imagem e som, gerando um .mp4 perfeito.\n"
            "[ ÁUDIO: ON ] -> O aplicativo descarta a imagem e processa apenas o .mp3, perfeito para ouvir no carro ou celular.\n\n"
            "PASSO 4: ARQUITETURA DE RENDERIZAÇÃO PARALELA E INTELIGENTE\n"
            "Na Versão 6.1e, o aplicativo identifica a origem do link (YouTube, Hotmart, etc.) e ajusta o paralelismo automaticamente. "
            "Ao iniciar um lote, todos os arquivos começam a ser baixados SIMULTANEAMENTE da internet para evitar que os links expirem. "
            "Ao chegarem em 100%, o aplicativo os coloca em uma fila indiana, usando a CPU para unir áudio e vídeo de um em um, sem travar sua máquina.\n"
        )
        txt.insert(tk.END, tutorial)
        txt.config(state=tk.DISABLED)
        
        btn_fechar = tk.Button(corpo, text="ENTENDI, FECHAR GUIA", command=janela.destroy, font=("Segoe UI", 9, "bold"), bg=COR_AMARELO, fg=COR_PRETO, relief=tk.FLAT, cursor="hand2", pady=5, padx=20)
        btn_fechar.pack(anchor="center")

#====================================================
# MODAL: CONFIGURAR
#====================================================
class ModalConfigurar:
    @staticmethod
    def abrir(parent):
        janela = tk.Toplevel(parent)
        janela.title("Configuração do Sistema - Diagnóstico Windows")
        janela.geometry("680x620")
        janela.minsize(620, 560)
        janela.configure(bg=COR_FUNDO)
        janela.transient(parent)
        janela.grab_set()
        
        ico = obter_caminho_icone()
        if ico:
            try: janela.iconbitmap(ico)
            except Exception: pass
                
        parent.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 340
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 310
        janela.geometry(f"+{px}+{py}")
        
        corpo = tk.Frame(janela, bg=COR_CONTAINER, bd=1, relief=tk.SOLID, padx=22, pady=20)
        corpo.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        lbl_tit = tk.Label(corpo, text="DIAGNÓSTICO DE DEPENDÊNCIAS", font=("Segoe UI", 15, "bold"), bg=COR_CONTAINER, fg=COR_AMARELO)
        lbl_tit.pack(anchor="w")
        
        lbl_sub = tk.Label(corpo, text="Ambiente exclusivo para Windows 10/11 (64-bit).\nO DOWN 6.1e requer os motores 'yt-dlp' (baixador) e 'ffmpeg' (mesclador e conversor MP3).", font=("Segoe UI", 9), bg=COR_CONTAINER, fg=COR_CINZA_TEXTO, justify="left")
        lbl_sub.pack(anchor="w", pady=(2, 12))
        
        tem_ytdlp = checar_executavel("yt-dlp")
        tem_ffmpeg = checar_executavel("ffmpeg")
        
        card_status = tk.Frame(corpo, bg=COR_PRETO, bd=1, relief=tk.SOLID, padx=15, pady=12)
        card_status.pack(fill=tk.X, pady=(0, 15))
        
        f_ytdlp = tk.Frame(card_status, bg=COR_PRETO)
        f_ytdlp.pack(fill=tk.X, pady=3)
        lbl_y1 = tk.Label(f_ytdlp, text="Motor de Download (yt-dlp.exe):", font=("Segoe UI", 9, "bold"), bg=COR_PRETO, fg=COR_BRANCO)
        lbl_y1.pack(side=tk.LEFT)
        cor_y = COR_VERDE_OK if tem_ytdlp else COR_VERMELHO
        txt_y = "INSTALADO E PRONTO" if tem_ytdlp else "NÃO ENCONTRADO"
        lbl_y2 = tk.Label(f_ytdlp, text=txt_y, font=("Segoe UI", 9, "bold"), bg=COR_PRETO, fg=cor_y)
        lbl_y2.pack(side=tk.RIGHT)
        
        f_ff = tk.Frame(card_status, bg=COR_PRETO)
        f_ff.pack(fill=tk.X, pady=3)
        lbl_f1 = tk.Label(f_ff, text="Processador de Mídia (ffmpeg.exe):", font=("Segoe UI", 9, "bold"), bg=COR_PRETO, fg=COR_BRANCO)
        lbl_f1.pack(side=tk.LEFT)
        cor_f = COR_VERDE_OK if tem_ffmpeg else COR_VERMELHO
        txt_f = "INSTALADO E PRONTO" if tem_ffmpeg else "NÃO ENCONTRADO"
        lbl_f2 = tk.Label(f_ff, text=txt_f, font=("Segoe UI", 9, "bold"), bg=COR_PRETO, fg=cor_f)
        lbl_f2.pack(side=tk.RIGHT)
        
        lbl_opcoes = tk.Label(corpo, text="OPÇÕES DE INSTALAÇÃO:", font=("Segoe UI", 10, "bold"), bg=COR_CONTAINER, fg=COR_AMARELO)
        lbl_opcoes.pack(anchor="w", pady=(5, 6))
        
        txt_inst = tk.Text(corpo, bg=COR_PRETO, fg=COR_BRANCO, font=("Consolas", 8), height=8, relief=tk.FLAT)
        txt_inst.pack(fill=tk.X, pady=(0, 10))
        
        if tem_ytdlp and tem_ffmpeg:
            txt_inst.insert(tk.END, "Tudo certo! Nenhuma instalação adicional é necessária. O DOWN 6.1e funcionará com força total.")
        else:
            txt_inst.insert(tk.END, "[!] Dependências ausentes identificadas no seu computador.\nClique no botão abaixo para fazer a instalação 100% automática ou veja o tutorial manual.")
            
        def instalar_automatico():
            btn_auto.config(state=tk.DISABLED, bg=COR_CONTAINER, fg=COR_CINZA_TEXTO, text="BAIXANDO COMPONENTES... AGUARDE")
            txt_inst.delete("1.0", tk.END)
            
            def worker():
                try:
                    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    if not checar_executavel("yt-dlp"):
                        txt_inst.insert(tk.END, "[1/2] Baixando yt-dlp.exe oficial do GitHub...\n")
                        txt_inst.see(tk.END)
                        url_ytdlp = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
                        dest_ytdlp = os.path.join(PASTA_APP, "yt-dlp.exe")
                        req = urllib.request.Request(url_ytdlp, headers={"User-Agent": user_agent})
                        with urllib.request.urlopen(req, timeout=30) as resp, open(dest_ytdlp, 'wb') as out_f:
                            shutil.copyfileobj(resp, out_f)
                        txt_inst.insert(tk.END, "yt-dlp.exe baixado e integrado ao programa!\n")
                        txt_inst.see(tk.END)
                        
                    if not checar_executavel("ffmpeg"):
                        txt_inst.insert(tk.END, "[2/2] Baixando binário oficial do FFmpeg Essentials...\n")
                        txt_inst.see(tk.END)
                        url_ffmpeg = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                        zip_tmp = os.path.join(PASTA_APP, "ffmpeg_tmp.zip")
                        req = urllib.request.Request(url_ffmpeg, headers={"User-Agent": user_agent})
                        with urllib.request.urlopen(req, timeout=60) as resp, open(zip_tmp, 'wb') as out_f:
                            shutil.copyfileobj(resp, out_f)
                        txt_inst.insert(tk.END, "Extraindo ffmpeg.exe...\n")
                        txt_inst.see(tk.END)
                        with zipfile.ZipFile(zip_tmp, 'r') as z:
                            for arq in z.namelist():
                                if arq.endswith("ffmpeg.exe"):
                                    with z.open(arq) as zf, open(os.path.join(PASTA_APP, "ffmpeg.exe"), 'wb') as df:
                                        shutil.copyfileobj(zf, df)
                                    break
                        if os.path.exists(zip_tmp):
                            os.remove(zip_tmp)
                        txt_inst.insert(tk.END, "ffmpeg.exe baixado e integrado ao programa!\n")
                        txt_inst.see(tk.END)
                        
                    txt_inst.insert(tk.END, "\n====================================\n")
                    txt_inst.insert(tk.END, "INSTALAÇÃO AUTOMÁTICA CONCLUÍDA!\n")
                    txt_inst.insert(tk.END, "====================================\n")
                    txt_inst.see(tk.END)
                    
                    lbl_y2.config(text="INSTALADO E PRONTO", fg=COR_VERDE_OK)
                    lbl_f2.config(text="INSTALADO E PRONTO", fg=COR_VERDE_OK)
                    btn_auto.config(state=tk.DISABLED, text="TUDO INSTALADO AUTOMATICAMENTE")
                    ModalMensagem.show(parent, "Sucesso", "Todas as dependências foram baixadas e configuradas automaticamente!", "info")
                except Exception as e:
                    txt_inst.insert(tk.END, f"\n[!] Falha no download automático: {e}\nUtilize o método manual.")
                    btn_auto.config(state=tk.NORMAL, text="TENTAR NOVAMENTE")
                    
            threading.Thread(target=worker, daemon=True).start()

        btn_auto = tk.Button(
            corpo, 
            text="INSTALAR TUDO AUTOMATICAMENTE (RECOMENDADO)", 
            command=instalar_automatico, 
            font=("Segoe UI", 10, "bold"), 
            bg=COR_AMARELO, 
            fg=COR_PRETO, 
            activebackground=COR_AMARELO_HOVER, 
            activeforeground=COR_PRETO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            pady=7
        )
        btn_auto.pack(fill=tk.X, pady=(0, 6))
        
        def abrir_tutorial_manual():
            msg = (
                "COMO INSTALAR MANUALMENTE NO WINDOWS:\n\n"
                "1. Baixe o 'yt-dlp.exe' no link oficial:\n"
                "https://github.com/yt-dlp/yt-dlp/releases/latest\n\n"
                "2. Baixe o 'ffmpeg' em:\n"
                "https://www.gyan.dev/ffmpeg/builds/\n\n"
                "3. Coloque os dois arquivos ('yt-dlp.exe' e 'ffmpeg.exe') exatamente dentro da mesma pasta onde está este aplicativo DOWN 6.1e.\n\n"
                "Feito isso, o sistema reconhecerá os dois instantaneamente!"
            )
            ModalMensagem.show(parent, "Instalação Manual Passo a Passo", msg, "info")

        btn_manual = tk.Button(
            corpo, 
            text="Como Baixar e Instalar Sozinho (Passo a Passo)", 
            command=abrir_tutorial_manual, 
            font=("Segoe UI", 9), 
            bg=COR_CONTAINER, 
            fg=COR_BRANCO, 
            relief=tk.SOLID, 
            bd=1, 
            cursor="hand2", 
            pady=5
        )
        btn_manual.pack(fill=tk.X, pady=(0, 10))
        
        btn_sair = tk.Button(corpo, text="FECHAR CONFIGURAÇÕES", command=janela.destroy, font=("Segoe UI", 9), bg=COR_PRETO, fg=COR_BRANCO, relief=tk.FLAT, cursor="hand2", pady=4)
        btn_sair.pack(anchor="center")

#====================================================
# SPLASH SCREEN COM ANIMAÇÃO CINEMATOGRÁFICA
#====================================================
class SplashScreen:
    def __init__(self, root, callback_pronto):
        self.root = root
        self.callback_pronto = callback_pronto
        self.tempo_restante = 10
        self.rodando = True
        
        self.splash = tk.Toplevel(root)
        self.splash.overrideredirect(True)
        self.splash.configure(bg=COR_FUNDO)
        
        ico = obter_caminho_icone()
        if ico:
            try: self.splash.iconbitmap(ico)
            except Exception: pass
                
        largura, altura = 720, 520
        sx = (self.splash.winfo_screenwidth() // 2) - (largura // 2)
        sy = (self.splash.winfo_screenheight() // 2) - (altura // 2)
        self.splash.geometry(f"{largura}x{altura}+{sx}+{sy}")
        
        self.canvas = tk.Canvas(self.splash, width=largura, height=360, bg=COR_FUNDO, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        lbl_marca = tk.Label(self.splash, text="DOWN 6.1e", font=("Segoe UI", 26, "bold"), bg=COR_FUNDO, fg=COR_AMARELO)
        lbl_marca.pack()
        
        lbl_autor = tk.Label(self.splash, text="Copyright (C) Out/2026 Swammy Léo Sussuarana", font=("Segoe UI", 10), bg=COR_FUNDO, fg=COR_BRANCO)
        lbl_autor.pack(pady=(2, 6))
        
        rodape = tk.Frame(self.splash, bg=COR_FUNDO, pady=10)
        rodape.pack(fill=tk.X, padx=35)
        
        self.lbl_contador = tk.Label(rodape, text="Iniciando em 10s...", font=("Segoe UI", 9), bg=COR_FUNDO, fg=COR_CINZA_TEXTO)
        self.lbl_contador.pack(side=tk.LEFT)
        
        btn_pular = tk.Button(
            rodape, 
            text="PULAR ABERTURA", 
            command=self.encerrar_splash, 
            font=("Segoe UI", 9, "bold"), 
            bg=COR_AMARELO, 
            fg=COR_PRETO, 
            activebackground=COR_AMARELO_HOVER, 
            activeforeground=COR_PRETO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            padx=16, 
            pady=4
        )
        btn_pular.pack(side=tk.RIGHT)
        
        self.angulo_rot = 0.0
        self.fase_pulso = 0.0
        self.animar_geometria()
        self.iniciar_contagem()
        
    def iniciar_contagem(self):
        if not self.rodando:
            return
        if self.tempo_restante > 0:
            self.lbl_contador.config(text=f"Iniciando em {self.tempo_restante}s...")
            self.tempo_restante -= 1
            self.splash.after(1000, self.iniciar_contagem)
        else:
            self.encerrar_splash()
            
    def gerar_pontos_hexagono(self, cx, cy, raio, angulo_offset):
        pontos = []
        for i in range(6):
            a = angulo_offset + (i * (math.pi / 3))
            px = cx + raio * math.cos(a)
            py = cy + (raio * 0.90) * math.sin(a)
            pontos.extend([px, py])
        return pontos
        
    def animar_geometria(self):
        if not self.rodando:
            return
        self.canvas.delete("all")
        self.angulo_rot += 0.02
        self.fase_pulso += 0.05
        
        cx, cy = 360, 180
        pulso = 1.0 + 0.08 * math.sin(self.fase_pulso)
        raio_orbita = 155 * pulso
        
        self.canvas.create_oval(cx - raio_orbita, cy - (raio_orbita * 0.75), cx + raio_orbita, cy + (raio_orbita * 0.75), outline=COR_CONTAINER, width=2)
        
        for i in range(4):
            ang = self.angulo_rot + (i * (math.pi / 2))
            ox = cx + raio_orbita * math.cos(ang)
            oy = cy + (raio_orbita * 0.75) * math.sin(ang)
            self.canvas.create_oval(ox - 4, oy - 4, ox + 4, oy + 4, fill=COR_AMARELO, outline=COR_BRANCO)
            
        pts_externos = self.gerar_pontos_hexagono(cx, cy, 115 * pulso, self.angulo_rot)
        self.canvas.create_polygon(pts_externos, fill="", outline=COR_AMARELO, width=3)
        
        pts_base = self.gerar_pontos_hexagono(cx, cy, 95, math.pi / 6)
        self.canvas.create_polygon(pts_base, fill=COR_CONTAINER, outline=COR_AMARELO, width=3)
        
        pts_nucleo = self.gerar_pontos_hexagono(cx, cy, 75, math.pi / 6)
        self.canvas.create_polygon(pts_nucleo, fill=COR_PRETO, outline=COR_AMARELO, width=2)
        
        desloc_seta = 6 * math.sin(self.fase_pulso * 2)
        self.canvas.create_line(cx, cy - 42 + desloc_seta, cx, cy - 18 + desloc_seta, fill=COR_BRANCO, width=7)
        
        p_seta = [
            cx - 24, cy - 10 + desloc_seta,
            cx + 24, cy - 10 + desloc_seta,
            cx, cy + 42 + desloc_seta
        ]
        self.canvas.create_polygon(p_seta, fill=COR_AMARELO, outline=COR_BRANCO, width=2)
        
        largura_feixe = 45 * pulso
        self.canvas.create_line(cx - largura_feixe, cy + 60, cx + largura_feixe, cy + 60, fill=COR_AMARELO, width=3)
        self.canvas.create_line(cx - (largura_feixe * 0.6), cy + 68, cx + (largura_feixe * 0.6), cy + 68, fill=COR_BRANCO, width=2)
        
        self.splash.after(30, self.animar_geometria)
        
    def encerrar_splash(self):
        if not self.rodando:
            return
        self.rodando = False
        self.splash.destroy()
        self.callback_pronto()

#====================================================
# MODAL DE AUTORIA & PNL
#====================================================
class ModalAutor:
    @staticmethod
    def abrir(parent):
        janela = tk.Toplevel(parent)
        janela.title("Sobre o Autor & Filosofia de Desenvolvimento")
        janela.geometry("680x640")
        janela.minsize(640, 580)
        janela.configure(bg=COR_FUNDO)
        janela.transient(parent)
        janela.grab_set()
        
        ico = obter_caminho_icone()
        if ico:
            try: janela.iconbitmap(ico)
            except Exception: pass
                
        parent.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 340
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 320
        janela.geometry(f"+{px}+{py}")
        
        corpo = tk.Frame(janela, bg=COR_CONTAINER, bd=1, relief=tk.SOLID, padx=25, pady=25)
        corpo.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        lbl_tit = tk.Label(corpo, text="TECNOLOGIA, PROPÓSITO E LIBERDADE", font=("Segoe UI", 16, "bold"), bg=COR_CONTAINER, fg=COR_AMARELO)
        lbl_tit.pack(anchor="w")
        
        lbl_sub = tk.Label(corpo, text="Desenvolvido por Swammy Léo Sussuarana", font=("Segoe UI", 11, "bold"), bg=COR_CONTAINER, fg=COR_BRANCO)
        lbl_sub.pack(anchor="w", pady=(2, 15))
        
        texto_pnl = (
            "Você certamente reconhece o imenso valor do seu tempo e a importância de ter ferramentas "
            "precisas, seguras e transparentes ao seu alcance. Quando a tecnologia é construída com "
            "respeito e excelência, ela simplesmente funciona sem travas, sem cobranças ocultas e sem pegadinhas.\n\n"
            "O DOWN 6.1e foi criado sob esse exato princípio: servir ao seu aprendizado e maximizar seus estudos "
            "com máxima velocidade e dignidade. Por isso, este software é, e continuará sendo, 100% GRATUITO PARA SEMPRE.\n\n"
            "Se esta solução economizou seu tempo, facilitou sua rotina e gerou valor real na sua jornada, "
            "você é convidado a exercer o princípio sagrado da Reciprocidade Consciente. Uma contribuição espontânea "
            "é um gesto voluntário de honra mútua que fortalece a manutenção e o desenvolvimento contínuo de novas tecnologias livres."
        )
        txt_box = tk.Text(corpo, bg=COR_CONTAINER, fg="#CBD5E1", font=("Segoe UI", 9), relief=tk.FLAT, wrap=tk.WORD, height=10)
        txt_box.insert(tk.END, texto_pnl)
        txt_box.config(state=tk.DISABLED)
        txt_box.pack(fill=tk.X, pady=(0, 15))
        
        btn_mp = tk.Button(
            corpo, 
            text="FAZER UMA CONTRIBUIÇÃO VOLUNTÁRIA (MERCADO PAGO)", 
            command=lambda: webbrowser.open("https://link.mercadopago.com.br/sussuarana"), 
            font=("Segoe UI", 10, "bold"), 
            bg=COR_AMARELO, 
            fg=COR_PRETO, 
            activebackground=COR_AMARELO_HOVER, 
            activeforeground=COR_PRETO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            pady=8
        )
        btn_mp.pack(fill=tk.X, pady=(0, 10))
        
        btn_wpp = tk.Button(
            corpo, 
            text="FALAR COM O AUTOR NO WHATSAPP BUSINESS", 
            command=lambda: webbrowser.open("https://wa.me/5561981951122"), 
            font=("Segoe UI", 9, "bold"), 
            bg="#059669", 
            fg=COR_BRANCO, 
            activebackground="#047857", 
            activeforeground=COR_BRANCO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            pady=7
        )
        btn_wpp.pack(fill=tk.X, pady=(0, 15))
        
        btn_fechar = tk.Button(
            corpo, 
            text="FECHAR JANELA", 
            command=janela.destroy, 
            font=("Segoe UI", 9), 
            bg=COR_PRETO, 
            fg=COR_BRANCO, 
            activebackground=COR_CONTAINER, 
            activeforeground=COR_BRANCO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            pady=4
        )
        btn_fechar.pack(anchor="center")

#====================================================
# APLICAÇÃO PRINCIPAL: DOWN 6.1e
#====================================================
class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DOWN 6.1e - Swammy Léo Sussuarana")
        self.root.geometry("980x900")
        self.root.minsize(800, 750)
        self.root.configure(bg=COR_FUNDO)
        
        pasta_padrao_win = obter_pasta_downloads_windows()
        
        self.formato_alvo = tk.StringVar(value="video")
        self.var_pasta_m = tk.StringVar(value=pasta_padrao_win)
        self.var_nome_m = tk.StringVar(value="")
        self.var_url_m = tk.StringVar(value="")
        self.var_prog_m_texto = tk.StringVar(value="Pronto para baixar...")
        self.em_download_manual = False
        
        self.pasta_global_lote = tk.StringVar(value=pasta_padrao_win)
        self.titulo_base_lote = tk.StringVar(value="")
        self.slots_lote = []
        self.em_download_lote = False
        self.sessao_log = []
        
        self.ffmpeg_semaphore = threading.Semaphore(1)
        self.processos_ativos = {}
        self.cancelado = False
        self.animando_conversao_manual = False
        self.animando_conversao_lote = False
        
        self.progresso_lote = {}
        
        self.configurar_estilos()
        self.construir_interface()

    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar", 
            troughcolor=COR_PRETO, 
            background=COR_AMARELO, 
            darkcolor=COR_AMARELO, 
            lightcolor=COR_AMARELO, 
            bordercolor=COR_CONTAINER, 
            thickness=14
        )

    def desenhar_logomarca(self, canvas, x, y):
        canvas.create_polygon(x, y-22, x+20, y-10, x+20, y+14, x, y+26, x-20, y+14, x-20, y-10, fill=COR_CONTAINER, outline=COR_AMARELO, width=2)
        canvas.create_polygon(x, y-16, x+14, y-7, x+14, y+10, x, y+19, x-14, y+10, x-14, y-7, fill=COR_PRETO, outline=COR_AMARELO, width=1)
        canvas.create_line(x, y-9, x, y+6, fill=COR_BRANCO, width=3)
        canvas.create_polygon(x-7, y+3, x+7, y+3, x, y+12, fill=COR_AMARELO)

    def construir_interface(self):
        header = tk.Frame(self.root, bg=COR_FUNDO, pady=10)
        header.pack(fill=tk.X, padx=20)
        
        canvas_logo = tk.Canvas(header, width=60, height=60, bg=COR_FUNDO, highlightthickness=0)
        canvas_logo.pack(side=tk.LEFT)
        self.desenhar_logomarca(canvas_logo, 30, 30)
        
        frame_textos = tk.Frame(header, bg=COR_FUNDO)
        frame_textos.pack(side=tk.LEFT, padx=(10, 0))
        
        lbl_down = tk.Label(frame_textos, text="DOWN 6.1e", font=("Segoe UI", 20, "bold"), bg=COR_FUNDO, fg=COR_AMARELO)
        lbl_down.pack(anchor="w")
        
        lbl_copy = tk.Label(frame_textos, text="Copyright (C) Out/2026 Swammy Léo Sussuarana", font=("Segoe UI", 9), bg=COR_FUNDO, fg=COR_BRANCO)
        lbl_copy.pack(anchor="w")
        
        frame_acoes_topo = tk.Frame(header, bg=COR_FUNDO)
        frame_acoes_topo.pack(side=tk.RIGHT)
        
        btn_como_usar = tk.Button(
            frame_acoes_topo, 
            text="COMO USAR", 
            command=lambda: ModalComoUsar.abrir(self.root), 
            font=("Segoe UI", 9, "bold"), 
            bg=COR_CONTAINER, 
            fg=COR_AMARELO, 
            activebackground=COR_AMARELO, 
            activeforeground=COR_PRETO, 
            relief=tk.SOLID, 
            bd=1, 
            cursor="hand2", 
            padx=12, 
            pady=4
        )
        btn_como_usar.pack(side=tk.LEFT, padx=(0, 6))
        
        btn_config = tk.Button(
            frame_acoes_topo, 
            text="CONFIGURAR", 
            command=lambda: ModalConfigurar.abrir(self.root), 
            font=("Segoe UI", 9, "bold"), 
            bg=COR_CONTAINER, 
            fg=COR_BRANCO, 
            activebackground=COR_AMARELO, 
            activeforeground=COR_PRETO, 
            relief=tk.SOLID, 
            bd=1, 
            cursor="hand2", 
            padx=12, 
            pady=4
        )
        btn_config.pack(side=tk.LEFT, padx=(0, 8))
        
        btn_engrenagem = tk.Button(
            frame_acoes_topo, 
            text="⚙", 
            command=lambda: ModalAutor.abrir(self.root), 
            font=("Segoe UI", 12), 
            bg=COR_CONTAINER, 
            fg=COR_AMARELO, 
            activebackground=COR_AMARELO, 
            activeforeground=COR_PRETO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            padx=12, 
            pady=1
        )
        btn_engrenagem.pack(side=tk.LEFT)
        
        frame_abas = tk.Frame(self.root, bg=COR_FUNDO)
        frame_abas.pack(fill=tk.X, padx=20, pady=(5, 5))
        
        self.btn_aba_manual = tk.Button(
            frame_abas, 
            text="MODO MANUAL", 
            command=self.mostrar_aba_manual, 
            font=("Segoe UI", 9, "bold"), 
            bg=COR_AMARELO, 
            fg=COR_PRETO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            padx=16, 
            pady=6
        )
        self.btn_aba_manual.pack(side=tk.LEFT, padx=(0, 5))
        
        self.btn_aba_lote = tk.Button(
            frame_abas, 
            text="FLUXO POR LOTE", 
            command=self.mostrar_aba_lote, 
            font=("Segoe UI", 9, "bold"), 
            bg=COR_CONTAINER, 
            fg=COR_BRANCO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            padx=16, 
            pady=6
        )
        self.btn_aba_lote.pack(side=tk.LEFT)
        
        frame_formatos = tk.Frame(frame_abas, bg=COR_FUNDO)
        frame_formatos.pack(side=tk.RIGHT)
        
        lbl_formato = tk.Label(frame_formatos, text="FORMATO DE SAÍDA:", font=("Segoe UI", 8, "bold"), bg=COR_FUNDO, fg=COR_BRANCO)
        lbl_formato.pack(side=tk.LEFT, padx=(0, 8))
        
        self.btn_fmt_video = tk.Button(
            frame_formatos, 
            text="VÍDEO : ON", 
            command=self.set_formato_video, 
            font=("Segoe UI", 8, "bold"), 
            bg=COR_AMARELO, 
            fg=COR_PRETO, 
            relief=tk.SOLID, 
            bd=1, 
            cursor="hand2", 
            padx=12, 
            pady=4
        )
        self.btn_fmt_video.pack(side=tk.LEFT, padx=(0, 5))
        
        self.btn_fmt_audio = tk.Button(
            frame_formatos, 
            text="ÁUDIO : OFF", 
            command=self.set_formato_audio, 
            font=("Segoe UI", 8, "bold"), 
            bg=COR_CONTAINER, 
            fg=COR_BRANCO, 
            relief=tk.SOLID, 
            bd=1, 
            cursor="hand2", 
            padx=12, 
            pady=4
        )
        self.btn_fmt_audio.pack(side=tk.LEFT)
        
        self.painel_manual = tk.Frame(self.root, bg=COR_FUNDO)
        self.painel_lote = tk.Frame(self.root, bg=COR_FUNDO)
        
        self.construir_painel_manual()
        self.construir_painel_lote()
        self.mostrar_aba_manual()

    def set_formato_video(self):
        self.formato_alvo.set("video")
        self.btn_fmt_video.config(text="VÍDEO : ON", bg=COR_AMARELO, fg=COR_PRETO)
        self.btn_fmt_audio.config(text="ÁUDIO : OFF", bg=COR_CONTAINER, fg=COR_BRANCO)

    def set_formato_audio(self):
        self.formato_alvo.set("audio")
        self.btn_fmt_video.config(text="VÍDEO : OFF", bg=COR_CONTAINER, fg=COR_BRANCO)
        self.btn_fmt_audio.config(text="ÁUDIO : ON", bg=COR_AMARELO, fg=COR_PRETO)

    def mostrar_aba_manual(self):
        self.painel_lote.pack_forget()
        self.painel_manual.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        self.btn_aba_manual.config(bg=COR_AMARELO, fg=COR_PRETO)
        self.btn_aba_lote.config(bg=COR_CONTAINER, fg=COR_BRANCO)

    def mostrar_aba_lote(self):
        self.painel_manual.pack_forget()
        self.painel_lote.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        self.btn_aba_lote.config(bg=COR_AMARELO, fg=COR_PRETO)
        self.btn_aba_manual.config(bg=COR_CONTAINER, fg=COR_BRANCO)

    #====================================================
    # CANCELAMENTO DE PROCESSOS E ANIMAÇÕES
    #====================================================
    def cancelar_processo(self):
        self.cancelado = True
        self.animando_conversao_manual = False
        self.animando_conversao_lote = False
        
        if getattr(self, 'lbl_overlay_manual', None): 
            self.lbl_overlay_manual.pack_forget()
        if getattr(self, 'lbl_overlay_lote', None): 
            self.lbl_overlay_lote.pack_forget()
        
        for p_list in self.processos_ativos.values():
            for p in p_list:
                try: p.kill()
                except: pass

    def animar_texto_conversao_manual(self):
        if getattr(self, 'animando_conversao_manual', False) and self.em_download_manual:
            cor_atual = self.lbl_overlay_manual.cget("fg")
            nova_cor = COR_BRANCO if cor_atual == COR_VERDE_OK else COR_VERDE_OK
            txt = "Convertendo os fragmentos de código para criar o arquivo final..." if self.formato_alvo.get() == "video" else "Convertendo e Montando Áudio final..."
            self.lbl_overlay_manual.config(text=txt, fg=nova_cor)
            
            if not self.lbl_overlay_manual.winfo_ismapped():
                self.lbl_overlay_manual.pack(pady=(5, 0))
                
            self.root.after(600, self.animar_texto_conversao_manual)
        else:
            if getattr(self, 'lbl_overlay_manual', None):
                self.lbl_overlay_manual.pack_forget()

    def animar_texto_conversao_lote(self):
        if getattr(self, 'animando_conversao_lote', False) and self.em_download_lote:
            cor_atual = self.lbl_overlay_lote.cget("fg")
            nova_cor = COR_BRANCO if cor_atual == COR_VERDE_OK else COR_VERDE_OK
            txt = "Convertendo os fragmentos de código para criar o arquivo final..." if self.formato_alvo.get() == "video" else "Convertendo e Montando Áudio final..."
            self.lbl_overlay_lote.config(text=txt, fg=nova_cor)
            
            if not self.lbl_overlay_lote.winfo_ismapped():
                self.lbl_overlay_lote.pack(fill=tk.X, pady=(10, 0))
                
            self.root.after(600, self.animar_texto_conversao_lote)
        else:
            if getattr(self, 'lbl_overlay_lote', None):
                self.lbl_overlay_lote.pack_forget()

    #====================================================
    # PAINEL 1: MODO MANUAL
    #====================================================
    def construir_painel_manual(self):
        card = tk.Frame(self.painel_manual, bg=COR_CONTAINER, bd=1, relief=tk.SOLID, padx=20, pady=15)
        card.pack(fill=tk.X, pady=4)
        
        lbl_p = tk.Label(card, text="DIRETÓRIO DE DESTINO:", font=("Segoe UI", 9, "bold"), bg=COR_CONTAINER, fg=COR_BRANCO)
        lbl_p.pack(anchor="w")
        
        fp = tk.Frame(card, bg=COR_CONTAINER)
        fp.pack(fill=tk.X, pady=(2, 10))
        
        ent_pasta = tk.Entry(fp, textvariable=self.var_pasta_m, font=("Segoe UI", 10), bg=COR_PRETO, fg=COR_BRANCO, insertbackground=COR_AMARELO, relief=tk.FLAT, bd=6)
        ent_pasta.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        btn_p = tk.Button(fp, text="Procurar...", command=lambda: self.selecionar_pasta(self.var_pasta_m), font=("Segoe UI", 9, "bold"), bg=COR_AMARELO, fg=COR_PRETO, relief=tk.FLAT, cursor="hand2", padx=12)
        btn_p.pack(side=tk.RIGHT, padx=(8, 0))
        
        lbl_n = tk.Label(card, text="NOME DO ARQUIVO (Opcional - deixe em branco para usar o nome original):", font=("Segoe UI", 9, "bold"), bg=COR_CONTAINER, fg=COR_BRANCO)
        lbl_n.pack(anchor="w")
        
        self.ent_nome_m = tk.Entry(card, font=("Segoe UI", 10), bg=COR_PRETO, fg=COR_PLACEHOLDER, insertbackground=COR_AMARELO, relief=tk.FLAT, bd=6)
        self.ent_nome_m.insert(0, PLACEHOLDER_NOME)
        self.ent_nome_m.pack(fill=tk.X, pady=(2, 10))
        
        def _foco_in_nome(e):
            if self.ent_nome_m.get() == PLACEHOLDER_NOME:
                self.ent_nome_m.delete(0, tk.END)
                self.ent_nome_m.config(fg=COR_BRANCO)
                
        def _foco_out_nome(e):
            if not self.ent_nome_m.get().strip():
                self.ent_nome_m.insert(0, PLACEHOLDER_NOME)
                self.ent_nome_m.config(fg=COR_PLACEHOLDER)
                
        self.ent_nome_m.bind("<FocusIn>", _foco_in_nome)
        self.ent_nome_m.bind("<FocusOut>", _foco_out_nome)
        
        lbl_u = tk.Label(card, text="LINK DA ORIGEM (URL):", font=("Segoe UI", 9, "bold"), bg=COR_CONTAINER, fg=COR_AMARELO)
        lbl_u.pack(anchor="w")
        
        self.ent_url_m = tk.Entry(card, textvariable=self.var_url_m, font=("Segoe UI", 10), bg=COR_PRETO, fg=COR_BRANCO, insertbackground=COR_AMARELO, relief=tk.FLAT, bd=6)
        self.ent_url_m.pack(fill=tk.X, pady=(2, 4))
        
        lbl_status = tk.Label(self.painel_manual, textvariable=self.var_prog_m_texto, font=("Segoe UI", 9, "bold"), bg=COR_FUNDO, fg=COR_AMARELO)
        lbl_status.pack(anchor="w", pady=(8, 2))
        
        self.bar_manual = ttk.Progressbar(self.painel_manual, style="Custom.Horizontal.TProgressbar", orient="horizontal", mode="determinate", maximum=100, value=0)
        self.bar_manual.pack(fill=tk.X)
        
        self.frame_acoes_m = tk.Frame(self.painel_manual, bg=COR_FUNDO)
        self.frame_acoes_m.pack(fill=tk.X, pady=10)
        
        self.btn_download_m = tk.Button(
            self.frame_acoes_m, 
            text="INICIAR DOWNLOAD UNITÁRIO", 
            command=self.disparar_download_manual, 
            font=("Segoe UI", 11, "bold"), 
            bg=COR_AMARELO, 
            fg=COR_PRETO, 
            activebackground=COR_AMARELO_HOVER, 
            activeforeground=COR_PRETO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            pady=8
        )
        self.btn_download_m.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        self.btn_limpar_m = tk.Button(
            self.frame_acoes_m, 
            text="LIMPAR", 
            command=self.limpar_modo_manual, 
            font=("Segoe UI", 10, "bold"), 
            bg=COR_CONTAINER, 
            fg=COR_BRANCO, 
            activebackground=COR_CARD_HOVER, 
            activeforeground=COR_AMARELO, 
            relief=tk.SOLID, 
            bd=1, 
            cursor="hand2", 
            padx=18, 
            pady=8
        )
        self.btn_limpar_m.pack(side=tk.RIGHT)
        
        self.frame_cancel_m = tk.Frame(self.painel_manual, bg=COR_FUNDO)
        
        self.btn_cancelar_m = tk.Button(
            self.frame_cancel_m,
            text="CANCELAR PROCESSO",
            command=self.cancelar_processo,
            font=("Segoe UI", 11, "bold"),
            bg=COR_VERMELHO,
            fg=COR_BRANCO,
            activebackground="#B91C1C",
            activeforeground=COR_BRANCO,
            relief=tk.FLAT,
            cursor="hand2",
            pady=8
        )
        self.btn_cancelar_m.pack(fill=tk.X)
        
        self.lbl_overlay_manual = tk.Label(self.frame_cancel_m, text="", font=("Segoe UI", 9, "bold"), bg=COR_FUNDO, fg=COR_VERDE_OK)
        self.lbl_overlay_manual.pack_forget()
        
        lbl_t = tk.Label(self.painel_manual, text="CONSOLE DE DETALHES", font=("Segoe UI", 8, "bold"), bg=COR_FUNDO, fg=COR_BRANCO)
        lbl_t.pack(anchor="w")
        
        ft = tk.Frame(self.painel_manual, bg=COR_PRETO, bd=1, relief=tk.SOLID)
        ft.pack(fill=tk.BOTH, expand=True, pady=(2, 10))
        
        self.txt_log_m = tk.Text(ft, bg=COR_PRETO, fg="#D1D5DB", font=("Consolas", 8), relief=tk.FLAT, wrap=tk.WORD)
        self.txt_log_m.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        sb = tk.Scrollbar(ft, command=self.txt_log_m.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log_m.config(yscrollcommand=sb.set)

    def limpar_modo_manual(self):
        self.var_pasta_m.set(obter_pasta_downloads_windows())
        self.ent_nome_m.delete(0, tk.END)
        self.ent_nome_m.insert(0, PLACEHOLDER_NOME)
        self.ent_nome_m.config(fg=COR_PLACEHOLDER)
        self.var_url_m.set("")
        self.var_prog_m_texto.set("Pronto para baixar...")
        self.bar_manual.configure(value=0, mode="determinate")
        self.txt_log_m.delete("1.0", tk.END)
        self.lbl_overlay_manual.pack_forget()
        self.frame_cancel_m.pack_forget()
        self.frame_acoes_m.pack(fill=tk.X, pady=10)
        self.ent_url_m.focus_set()
        ToastNotification.show(self.root, "Modo Manual Limpo", "Todos os campos foram restaurados para o padrão.")

    #====================================================
    # PAINEL 2: FLUXO POR LOTE COM GRID ALINHADO (HARMONIA)
    #====================================================
    def construir_painel_lote(self):
        top_bar = tk.Frame(self.painel_lote, bg=COR_CONTAINER, bd=1, relief=tk.SOLID, padx=12, pady=6)
        top_bar.pack(fill=tk.X, pady=(0, 4))
        
        top_bar.columnconfigure(1, weight=1)
        
        lbl_pg = tk.Label(top_bar, text="Pasta Padrão:", font=("Segoe UI", 8, "bold"), bg=COR_CONTAINER, fg=COR_BRANCO, anchor="w")
        lbl_pg.grid(row=0, column=0, sticky="w", pady=3)
        
        ent_pg = tk.Entry(top_bar, textvariable=self.pasta_global_lote, font=("Segoe UI", 8), bg=COR_PRETO, fg=COR_BRANCO, insertbackground=COR_AMARELO, relief=tk.FLAT, bd=3)
        ent_pg.grid(row=0, column=1, sticky="we", padx=6, pady=3)
        
        btn_sel = tk.Button(top_bar, text="Procurar...", command=lambda: self.selecionar_pasta(self.pasta_global_lote), font=("Segoe UI", 8, "bold"), bg=COR_AMARELO, fg=COR_PRETO, relief=tk.FLAT, cursor="hand2")
        btn_sel.grid(row=0, column=2, padx=(0, 6), pady=3, sticky="we")
        
        btn_replicar_p = tk.Button(top_bar, text="Replicar Pasta para Todos", command=self.replicar_pasta_lote, font=("Segoe UI", 8, "bold"), bg=COR_CONTAINER, fg=COR_AMARELO, relief=tk.SOLID, bd=1, cursor="hand2")
        btn_replicar_p.grid(row=0, column=3, pady=3, sticky="we")
        
        lbl_tg = tk.Label(top_bar, text="Título Base:", font=("Segoe UI", 8, "bold"), bg=COR_CONTAINER, fg=COR_AMARELO, anchor="w")
        lbl_tg.grid(row=1, column=0, sticky="w", pady=3)
        
        ent_tg = tk.Entry(top_bar, textvariable=self.titulo_base_lote, font=("Segoe UI", 8), bg=COR_PRETO, fg=COR_BRANCO, insertbackground=COR_AMARELO, relief=tk.FLAT, bd=3)
        ent_tg.grid(row=1, column=1, sticky="we", padx=6, pady=3)
        
        btn_replicar_t = tk.Button(top_bar, text="Replicar Título", command=self.replicar_titulo_lote, font=("Segoe UI", 8, "bold"), bg=COR_AMARELO, fg=COR_PRETO, relief=tk.FLAT, cursor="hand2")
        btn_replicar_t.grid(row=1, column=2, padx=(0, 6), pady=3, sticky="we")
        
        btn_limpar_lote_topo = tk.Button(top_bar, text="Limpar Lote", command=self.limpar_modo_lote, font=("Segoe UI", 8, "bold"), bg=COR_CONTAINER, fg=COR_BRANCO, relief=tk.SOLID, bd=1, cursor="hand2")
        btn_limpar_lote_topo.grid(row=1, column=3, pady=3, sticky="we")
        
        grid_container = tk.Frame(self.painel_lote, bg=COR_FUNDO)
        grid_container.pack(fill=tk.BOTH, expand=True)
        grid_container.rowconfigure(0, weight=85)
        grid_container.rowconfigure(1, weight=15)
        grid_container.columnconfigure(0, weight=1)
        
        frame_scroll = tk.Frame(grid_container, bg=COR_FUNDO)
        frame_scroll.grid(row=0, column=0, sticky="nsew", pady=(0, 2))
        
        self.canvas_slots = tk.Canvas(frame_scroll, bg=COR_FUNDO, highlightthickness=0)
        scrollbar_lote = tk.Scrollbar(frame_scroll, orient="vertical", command=self.canvas_slots.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas_slots, bg=COR_FUNDO)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas_slots.configure(scrollregion=self.canvas_slots.bbox("all")))
        
        self.janela_canvas_id = self.canvas_slots.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_slots.bind("<Configure>", lambda e: self.canvas_slots.itemconfig(self.janela_canvas_id, width=e.width))
        
        self.canvas_slots.configure(yscrollcommand=scrollbar_lote.set)
        self.canvas_slots.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_lote.pack(side=tk.RIGHT, fill=tk.Y)
        
        def _executar_rolagem_global(event):
            if self.canvas_slots.winfo_exists():
                self.canvas_slots.yview_scroll(int(-1 * (event.delta / 120)), "units")
                
        self.canvas_slots.bind_all("<MouseWheel>", _executar_rolagem_global)
        
        self.slots_lote = []
        for i in range(1, 11):
            slot = self.criar_slot_lote(self.scrollable_frame, i)
            self.slots_lote.append(slot)
            
        frame_baixo = tk.Frame(grid_container, bg=COR_FUNDO)
        frame_baixo.grid(row=1, column=0, sticky="nsew", pady=(2, 2))
        frame_baixo.rowconfigure(0, weight=1)
        frame_baixo.columnconfigure(0, weight=8) 
        frame_baixo.columnconfigure(1, weight=2) 
        
        painel_logs = tk.Frame(frame_baixo, bg=COR_FUNDO)
        painel_logs.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.painel_botoes_lote = tk.Frame(frame_baixo, bg=COR_FUNDO)
        self.painel_botoes_lote.grid(row=0, column=1, sticky="nsew")
        
        self.var_prog_lote_txt = tk.StringVar(value="Lote aguardando preenchimento...")
        lbl_prog_l = tk.Label(painel_logs, textvariable=self.var_prog_lote_txt, font=("Segoe UI", 8, "bold"), bg=COR_FUNDO, fg=COR_AMARELO)
        lbl_prog_l.pack(anchor="w")
        
        self.bar_lote = ttk.Progressbar(painel_logs, style="Custom.Horizontal.TProgressbar", orient="horizontal", mode="determinate", maximum=100, value=0)
        self.bar_lote.pack(fill=tk.X, pady=(2, 5))
        
        frame_txt_lote = tk.Frame(painel_logs, bg=COR_PRETO, bd=1, relief=tk.SOLID)
        frame_txt_lote.pack(fill=tk.BOTH, expand=True)
        
        self.txt_log_l = tk.Text(frame_txt_lote, bg=COR_PRETO, fg="#D1D5DB", font=("Consolas", 8), relief=tk.FLAT, wrap=tk.WORD, height=3)
        self.txt_log_l.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=2)
        
        sb_l = tk.Scrollbar(frame_txt_lote, command=self.txt_log_l.yview)
        sb_l.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log_l.config(yscrollcommand=sb_l.set)

        self.btn_download_lote = tk.Button(
            self.painel_botoes_lote, 
            text="INICIAR\nEM LOTE", 
            command=self.disparar_download_lote, 
            font=("Segoe UI", 9, "bold"), 
            bg=COR_AMARELO, 
            fg=COR_PRETO, 
            activebackground=COR_AMARELO_HOVER, 
            activeforeground=COR_PRETO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            pady=10
        )
        self.btn_download_lote.pack(fill=tk.X, pady=(15, 5))

        self.btn_limpar_lote_baixo = tk.Button(
            self.painel_botoes_lote, 
            text="LIMPAR TODO LOTE", 
            command=self.limpar_modo_lote, 
            font=("Segoe UI", 8, "bold"), 
            bg=COR_CONTAINER, 
            fg=COR_BRANCO, 
            activebackground=COR_CARD_HOVER, 
            activeforeground=COR_AMARELO, 
            relief=tk.SOLID, 
            bd=1, 
            cursor="hand2", 
            pady=6
        )
        self.btn_limpar_lote_baixo.pack(fill=tk.X)
        
        self.btn_cancelar_lote = tk.Button(
            self.painel_botoes_lote,
            text="CANCELAR\nPROCESSO",
            command=self.cancelar_processo,
            font=("Segoe UI", 9, "bold"),
            bg=COR_VERMELHO,
            fg=COR_BRANCO,
            activebackground="#B91C1C",
            activeforeground=COR_BRANCO,
            relief=tk.FLAT,
            cursor="hand2",
            pady=12
        )
        self.btn_cancelar_lote.pack_forget()
        
        self.lbl_overlay_lote = tk.Label(self.painel_botoes_lote, text="", font=("Segoe UI", 9, "bold"), bg=COR_FUNDO, fg=COR_VERDE_OK, wraplength=160, justify="center")
        self.lbl_overlay_lote.pack_forget()

    def criar_slot_lote(self, parent, indice: int) -> dict:
        box = tk.Frame(parent, bg=COR_CONTAINER, highlightthickness=1, highlightbackground=COR_PLACEHOLDER, highlightcolor=COR_PLACEHOLDER, bd=0, padx=10, pady=6)
        box.pack(fill=tk.X, pady=3, padx=4)
        
        v_ativo = tk.BooleanVar(value=False)
        v_url = tk.StringVar(value="")
        v_pasta = tk.StringVar(value=self.pasta_global_lote.get())
        v_status = tk.StringVar(value="Pendente")
        v_duracao = tk.StringVar(value="")
        
        linha1 = tk.Frame(box, bg=COR_CONTAINER)
        linha1.pack(fill=tk.X)
        
        chk = tk.Checkbutton(
            linha1, 
            text=f"Item {indice:02d}", 
            variable=v_ativo, 
            font=("Segoe UI", 9, "bold"), 
            bg=COR_CONTAINER, 
            fg=COR_AMARELO, 
            selectcolor=COR_PRETO, 
            activebackground=COR_CONTAINER, 
            activeforeground=COR_AMARELO
        )
        chk.pack(side=tk.LEFT, padx=(0, 8))
        
        frame_status = tk.Frame(linha1, bg=COR_CONTAINER)
        frame_status.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))
        
        lbl_s = tk.Label(frame_status, textvariable=v_status, font=("Segoe UI", 8, "bold"), bg=COR_CONTAINER, fg=COR_CINZA_TEXTO)
        lbl_s.pack(side=tk.LEFT, anchor="e")
        
        cv_status = tk.Canvas(frame_status, width=30, height=30, bg=COR_CONTAINER, highlightthickness=0)
        cv_status.pack(side=tk.RIGHT, anchor="e", pady=(2, 0), padx=(4,0))
        
        def atualizar_visual(estado):
            cv_status.delete("all")
            if estado == "vazio" or estado == "pendente":
                cor_borda = COR_PLACEHOLDER
                glow = COR_PLACEHOLDER
                inner = "#333333"
            elif estado == "baixando":
                cor_borda = COR_AMARELO
                glow = COR_AMARELO
                inner = COR_AMARELO
            elif estado == "concluido":
                cor_borda = COR_VERDE_OK
                glow = COR_VERDE_OK
                inner = COR_VERDE_OK
            elif estado == "erro":
                cor_borda = COR_VERMELHO
                glow = COR_VERMELHO
                inner = COR_VERMELHO
            else:
                cor_borda = COR_PLACEHOLDER
                glow = COR_PLACEHOLDER
                inner = "#333333"

            box.config(highlightbackground=cor_borda, highlightcolor=cor_borda)
            
            cv_status.create_oval(2, 2, 28, 28, fill=glow, outline="")
            cv_status.create_oval(5, 5, 25, 25, fill=COR_PRETO, outline="")
            cv_status.create_oval(7, 7, 23, 23, fill=inner, outline="")
            cv_status.create_oval(10, 10, 14, 13, fill="#FFFFFF", outline="")
            
        atualizar_visual("vazio")
        
        frame_campos_linha1 = tk.Frame(linha1, bg=COR_CONTAINER)
        frame_campos_linha1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        frame_nome = tk.Frame(frame_campos_linha1, bg=COR_CONTAINER)
        frame_nome.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        lbl_n = tk.Label(frame_nome, text="Nome do Arquivo (Opcional - Vazio = Título Original):", font=("Segoe UI", 8, "bold"), bg=COR_CONTAINER, fg=COR_BRANCO)
        lbl_n.pack(anchor="w")
        
        ent_n = tk.Entry(frame_nome, font=("Segoe UI", 9), bg=COR_PRETO, fg=COR_PLACEHOLDER, insertbackground=COR_AMARELO, relief=tk.FLAT, bd=3)
        ent_n.insert(0, PLACEHOLDER_NOME)
        ent_n.pack(fill=tk.X, pady=(1, 0))
        
        def _f_in(e, ent=ent_n):
            if ent.get() == PLACEHOLDER_NOME:
                ent.delete(0, tk.END)
                ent.config(fg=COR_BRANCO)
                
        def _f_out(e, ent=ent_n):
            if not ent.get().strip():
                ent.insert(0, PLACEHOLDER_NOME)
                ent.config(fg=COR_PLACEHOLDER)
                
        ent_n.bind("<FocusIn>", _f_in)
        ent_n.bind("<FocusOut>", _f_out)
        
        frame_pasta = tk.Frame(frame_campos_linha1, bg=COR_CONTAINER)
        frame_pasta.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        lbl_p = tk.Label(frame_pasta, text="Pasta de Destino:", font=("Segoe UI", 8, "bold"), bg=COR_CONTAINER, fg=COR_BRANCO)
        lbl_p.pack(anchor="w")
        
        box_p_btn = tk.Frame(frame_pasta, bg=COR_CONTAINER)
        box_p_btn.pack(fill=tk.X, pady=(1, 0))
        
        ent_p = tk.Entry(box_p_btn, textvariable=v_pasta, font=("Segoe UI", 8), bg=COR_PRETO, fg=COR_BRANCO, insertbackground=COR_AMARELO, relief=tk.FLAT, bd=3)
        ent_p.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        btn_sel_ind = tk.Button(box_p_btn, text="...", command=lambda v=v_pasta: self.selecionar_pasta(v), font=("Segoe UI", 7, "bold"), bg=COR_AMARELO, fg=COR_PRETO, relief=tk.FLAT, cursor="hand2", padx=5)
        btn_sel_ind.pack(side=tk.RIGHT, padx=(4, 0))
        
        linha2 = tk.Frame(box, bg=COR_CONTAINER)
        linha2.pack(fill=tk.X, pady=(5, 1))
        
        frame_labels_u = tk.Frame(linha2, bg=COR_CONTAINER)
        frame_labels_u.pack(fill=tk.X)
        
        lbl_u = tk.Label(frame_labels_u, text="Link da Origem (URL):", font=("Segoe UI", 8, "bold"), bg=COR_CONTAINER, fg=COR_AMARELO)
        lbl_u.pack(side=tk.LEFT)
        
        lbl_duracao = tk.Label(frame_labels_u, textvariable=v_duracao, font=("Segoe UI", 8, "bold"), bg=COR_CONTAINER, fg=COR_CINZA_TEXTO)
        lbl_duracao.pack(side=tk.LEFT, padx=(20, 0))
        
        box_url_btn = tk.Frame(linha2, bg=COR_CONTAINER)
        box_url_btn.pack(fill=tk.X, pady=(1, 0))
        
        ent_u = tk.Entry(box_url_btn, textvariable=v_url, font=("Segoe UI", 9), bg=COR_PRETO, fg=COR_BRANCO, insertbackground=COR_AMARELO, relief=tk.FLAT, bd=4)
        ent_u.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def _limpar_este_slot():
            v_ativo.set(False)
            ent_n.delete(0, tk.END)
            ent_n.insert(0, PLACEHOLDER_NOME)
            ent_n.config(fg=COR_PLACEHOLDER)
            v_pasta.set(self.pasta_global_lote.get())
            v_url.set("")
            v_status.set("Pendente")
            v_duracao.set("")
            lbl_s.config(fg=COR_CINZA_TEXTO)
            atualizar_visual("vazio")
            
        btn_limpar_ind = tk.Button(
            box_url_btn, 
            text="🗑 LIMPAR", 
            command=_limpar_este_slot, 
            font=("Segoe UI", 8), 
            bg=COR_PRETO, 
            fg=COR_BRANCO, 
            activebackground=COR_CARD_HOVER, 
            activeforeground=COR_AMARELO, 
            relief=tk.FLAT, 
            cursor="hand2", 
            padx=6
        )
        btn_limpar_ind.pack(side=tk.RIGHT, padx=(6, 0))
        
        return {
            "id": indice,
            "ativo": v_ativo,
            "ent_nome": ent_n,
            "url": v_url,
            "pasta": v_pasta,
            "status": v_status,
            "lbl_status": lbl_s,
            "duracao": v_duracao,
            "set_visual": atualizar_visual,
            "btn_limpar": btn_limpar_ind,
            "box": box
        }

    def replicar_pasta_lote(self):
        pg = self.pasta_global_lote.get()
        for s in self.slots_lote:
            s["pasta"].set(pg)
        ToastNotification.show(self.root, "Pasta Replicada", "O diretório foi aplicado a todos os 10 itens.")

    def replicar_titulo_lote(self):
        texto_puro = self.titulo_base_lote.get().strip()
        for s in self.slots_lote:
            s["ent_nome"].delete(0, tk.END)
            if texto_puro:
                s["ent_nome"].insert(0, texto_puro)
                s["ent_nome"].config(fg=COR_BRANCO)
            else:
                s["ent_nome"].insert(0, PLACEHOLDER_NOME)
                s["ent_nome"].config(fg=COR_PLACEHOLDER)
            s["ativo"].set(False)
        ToastNotification.show(self.root, "Título Replicado", "Texto replicado e todos os 10 itens desmarcados.")

    def limpar_modo_lote(self):
        padrao_pasta = obter_pasta_downloads_windows()
        self.pasta_global_lote.set(padrao_pasta)
        self.titulo_base_lote.set("")
        for s in self.slots_lote:
            s["ativo"].set(False)
            s["ent_nome"].delete(0, tk.END)
            s["ent_nome"].insert(0, PLACEHOLDER_NOME)
            s["ent_nome"].config(fg=COR_PLACEHOLDER)
            s["url"].set("")
            s["pasta"].set(padrao_pasta)
            s["status"].set("Pendente")
            s["duracao"].set("")
            s["lbl_status"].config(fg=COR_CINZA_TEXTO)
            s["set_visual"]("vazio")
            
        self.var_prog_lote_txt.set("Lote aguardando preenchimento...")
        self.bar_lote.configure(value=0, mode="determinate")
        self.txt_log_l.delete("1.0", tk.END)
        self.lbl_overlay_lote.pack_forget()
        self.canvas_slots.yview_moveto(0)
        ToastNotification.show(self.root, "Lote Limpo", "Todos os 10 itens foram restaurados para o padrão.")

    def selecionar_pasta(self, variavel):
        caminho = filedialog.askdirectory(initialdir=variavel.get(), title="Selecione o Diretório")
        if caminho:
            variavel.set(caminho)

    #====================================================
    # LÓGICA DE DOWNLOAD ARQUITETURA 6.1e
    #====================================================
    def executar_download_item(self, id_sessao: str, pasta: str, nome: str, url: str, cb_progresso=None, cb_log=None, is_lote=False) -> tuple:
        pasta = pasta.replace('\n', '').replace('\r', '').strip()
        nome = nome.replace('\n', '').replace('\r', '').strip()
        url = url.replace('\n', '').replace('\r', '').strip()
        
        os.makedirs(pasta, exist_ok=True)
        formato_selecionado = self.formato_alvo.get()
        ext_alvo = "mp3" if formato_selecionado == "audio" else "mp4"
        
        flags_criacao = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        cmd_ytdlp = obter_comando("yt-dlp")
        cmd_ffmpeg = obter_comando("ffmpeg")
        
        eh_hotmart = "hotmart" in url.lower() or ".m3u8" in url.lower()
        eh_youtube = "youtube.com" in url.lower() or "youtu.be" in url.lower()
        
        headers = ["--referer", "https://hotmart.com/", "--add-header", "Origin: https://hotmart.com"] if eh_hotmart else []
        
        if cb_progresso: cb_progresso(0, "Buscando metadados...")
        
        cmd_meta = [cmd_ytdlp, "--print", "%(duration_string)s||%(title)s"] + headers + [url]
        proc_meta = subprocess.run(cmd_meta, capture_output=True, text=True, creationflags=flags_criacao)
        meta_out = proc_meta.stdout.strip().split('||')
        
        dur_str = meta_out[0] if len(meta_out) > 0 and meta_out[0] else ""
        real_title = meta_out[1] if len(meta_out) > 1 and meta_out[1] else "Midia Original"
        
        nome_final = nome if nome and nome != PLACEHOLDER_NOME else real_title
        nome_final = re.sub(r'[\\/*?:"<>|\n\r\t]', '', nome_final).strip()
        arquivo_final = os.path.join(pasta, f"{nome_final}.{ext_alvo}")
        
        if cb_log: cb_log(f"-> Metadados Carregados: Arquivo='{nome_final}.{ext_alvo}', Duração='{dur_str}'")
        
        if id_sessao not in self.processos_ativos:
            self.processos_ativos[id_sessao] = []
            
        temp_dir = os.path.join(pasta, f".temp_down6_{id_sessao}_{int(time.time())}")
        os.makedirs(temp_dir, exist_ok=True)
        
        if is_lote:
            frag_count = "10" if eh_youtube else "3"
        else:
            frag_count = "16" if eh_youtube else "10"
        
        def rodar_cmd(cmd, weight, start_pct):
            p_obj = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore', bufsize=1, creationflags=flags_criacao)
            self.processos_ativos[id_sessao].append(p_obj)
            
            for linha in iter(p_obj.stdout.readline, ''):
                if self.cancelado: break
                l = linha.strip()
                if not l: continue
                
                if "HTTP Error 403: Forbidden" in l:
                    l += " (Acesso negado ou token do link expirado)"
                    
                is_prog = bool(re.search(r'\[download\]\s+(\d+\.?\d*)%', l))
                ignorar_no_log = is_prog and ("ETA" in l or "frag" in l) and "Destination:" not in l
                
                if cb_progresso and is_prog:
                    match = re.search(r'\[download\]\s+(\d+\.?\d*)%', l)
                    if match:
                        try:
                            p = float(match.group(1))
                            overall = start_pct + (p / 100.0 * weight)
                            msg_t = f"{p:.1f}%"
                            cb_progresso(overall, msg_t)
                        except: pass
                        
                if cb_log and not ignorar_no_log:
                    cb_log(l)
                    
            p_obj.stdout.close()
            return p_obj.wait() == 0 if not self.cancelado else False

        try:
            if formato_selecionado == "audio":
                if cb_progresso: cb_progresso(0, "Baixando Áudio...")
                cmd_a = [cmd_ytdlp, "--newline", "--no-playlist", "--concurrent-fragments", frag_count, "-f", "bestaudio", "-o", os.path.join(temp_dir, "audio.%(ext)s")] + headers + [url]
                if not rodar_cmd(cmd_a, 90, 0): return False, "", "", ""
                
                if cb_progresso: cb_progresso(90, "Aguardando Renderização...")
                self.ffmpeg_semaphore.acquire()
                try:
                    if self.cancelado: return False, "", "", ""
                    if cb_progresso: cb_progresso(91, "Convertendo e Montando Áudio final...")
                    
                    audio_files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("audio.")]
                    if not audio_files: return False, "", "", ""
                    
                    cmd_ff = [cmd_ffmpeg, "-i", audio_files[0], "-q:a", "0", "-y", arquivo_final]
                    pff = subprocess.Popen(cmd_ff, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=flags_criacao)
                    self.processos_ativos[id_sessao].append(pff)
                    while pff.poll() is None:
                        if self.cancelado:
                            pff.kill()
                            break
                        time.sleep(0.5)
                    if pff.returncode != 0 or self.cancelado: return False, "", "", ""
                finally:
                    self.ffmpeg_semaphore.release()
                    
            else: 
                if cb_progresso: cb_progresso(0, "Baixando Vídeo...")
                cmd_v = [cmd_ytdlp, "--newline", "--no-playlist", "--concurrent-fragments", frag_count, "-f", "bestvideo", "-o", os.path.join(temp_dir, "video.%(ext)s")] + headers + [url]
                ok_v = rodar_cmd(cmd_v, 45, 0)
                
                if cb_progresso: cb_progresso(45, "Baixando Áudio...")
                cmd_a = [cmd_ytdlp, "--newline", "--no-playlist", "--concurrent-fragments", frag_count, "-f", "bestaudio", "-o", os.path.join(temp_dir, "audio.%(ext)s")] + headers + [url]
                ok_a = rodar_cmd(cmd_a, 45, 45)
                
                if ok_v and ok_a and not self.cancelado:
                    if cb_progresso: cb_progresso(90, "Aguardando Renderização...")
                    self.ffmpeg_semaphore.acquire()
                    try:
                        if self.cancelado: return False, "", "", ""
                        if cb_progresso: cb_progresso(91, "Unindo Vídeo e Áudio...")
                        
                        v_f = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("video.")]
                        a_f = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("audio.")]
                        if not v_f or not a_f: return False, "", "", ""
                        
                        cmd_ff = [cmd_ffmpeg, "-i", v_f[0], "-i", a_f[0], "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", arquivo_final]
                        pff = subprocess.Popen(cmd_ff, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=flags_criacao)
                        self.processos_ativos[id_sessao].append(pff)
                        while pff.poll() is None:
                            if self.cancelado:
                                pff.kill()
                                break
                            time.sleep(0.5)
                        if pff.returncode != 0 or self.cancelado: return False, "", "", ""
                    finally:
                        self.ffmpeg_semaphore.release()
                elif not self.cancelado:
                    if cb_log: cb_log("-> Tentando fallback unificado (arquivo já mesclado na nuvem)...")
                    if cb_progresso: cb_progresso(0, "Baixando Arquivo Único...")
                    cmd_b = [cmd_ytdlp, "--newline", "--no-playlist", "--concurrent-fragments", frag_count, "-f", "best", "-o", arquivo_final] + headers + [url]
                    if not rodar_cmd(cmd_b, 98, 0): return False, "", "", ""

            if cb_progresso: cb_progresso(100, "Concluído")
            return True, nome_final, ext_alvo, dur_str

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            self.processos_ativos.pop(id_sessao, None)

    #====================================================
    # DISPARO MODO MANUAL
    #====================================================
    def disparar_download_manual(self):
        if not checar_executavel("yt-dlp"):
            ModalMensagem.show(self.root, "Configuração Necessária", "O motor 'yt-dlp' não está instalado!\nClique no botão 'CONFIGURAR' no topo direito para instalar automaticamente.", "erro")
            return
            
        if self.em_download_manual or self.em_download_lote:
            ModalMensagem.show(self.root, "Aguarde", "Já existe um processo em andamento!", "aviso")
            return
            
        p = self.var_pasta_m.get().replace('\n', '').replace('\r', '').strip()
        n = self.ent_nome_m.get().replace('\n', '').replace('\r', '').strip()
        u = self.var_url_m.get().replace('\n', '').replace('\r', '').strip()
        
        if not p:
            ModalMensagem.show(self.root, "Erro", "Por favor, selecione uma pasta de destino válida.", "erro")
            return
        if not u:
            ModalMensagem.show(self.root, "Erro", "Cole o link do arquivo para download.", "erro")
            self.ent_url_m.focus_set()
            return
            
        self.em_download_manual = True
        self.cancelado = False
        self.animando_conversao_manual = False
        self.lbl_overlay_manual.pack_forget()
        self.btn_limpar_m.config(state=tk.DISABLED)
        
        self.txt_log_m.delete("1.0", tk.END)
        self.sessao_log.clear()
        
        self.frame_acoes_m.pack_forget()
        self.frame_cancel_m.pack(fill=tk.X, pady=10)
        
        def worker():
            def cb_p(pct, msg):
                self.root.after(0, lambda: self.bar_manual.configure(value=pct))
                self.root.after(0, lambda: self.var_prog_m_texto.set(msg))
                
                if pct >= 90 and pct < 100:
                    if not getattr(self, 'animando_conversao_manual', False):
                        self.animando_conversao_manual = True
                        self.root.after(0, lambda: self.bar_manual.configure(mode="indeterminate"))
                        self.root.after(0, lambda: self.bar_manual.start(15))
                        self.root.after(0, self.animar_texto_conversao_manual)
                        
            def cb_l(msg):
                self.sessao_log.append(msg)
                self.root.after(0, lambda: self.txt_log_m.insert(tk.END, msg + "\n"))
                self.root.after(0, lambda: self.txt_log_m.see(tk.END))
                
            ok, nome_gerado, ext_gerada, _ = self.executar_download_item("manual_1", p, n, u, cb_progresso=cb_p, cb_log=cb_l, is_lote=False)
            
            self.em_download_manual = False
            self.animando_conversao_manual = False
            
            self.root.after(0, lambda: self.lbl_overlay_manual.pack_forget())
            self.root.after(0, lambda: self.bar_manual.stop())
            self.root.after(0, lambda: self.bar_manual.configure(mode="determinate"))
            
            self.root.after(0, lambda: self.frame_cancel_m.pack_forget())
            self.root.after(0, lambda: self.frame_acoes_m.pack(fill=tk.X, pady=10))
            self.root.after(0, lambda: self.btn_limpar_m.config(state=tk.NORMAL))
            
            if self.cancelado:
                self.root.after(0, lambda: self.bar_manual.configure(value=0))
                self.root.after(0, lambda: self.var_prog_m_texto.set("Processo Cancelado pelo Usuário."))
                return

            if ok:
                self.root.after(0, lambda: self.bar_manual.configure(value=100))
                self.root.after(0, lambda: self.var_prog_m_texto.set("Download Concluído com Sucesso! (100%)"))
                self.var_url_m.set("")
                self.root.after(0, lambda: self.exibir_modal_finalizacao("Processo Finalizado", f"O arquivo {nome_gerado}.{ext_gerada} foi baixado e salvo com sucesso!", False))
            else:
                self.root.after(0, lambda: self.bar_manual.configure(value=0))
                self.root.after(0, lambda: self.var_prog_m_texto.set("Falha no download."))
                self.root.after(0, lambda: self.exibir_modal_finalizacao("Falha no Processo", "Não foi possível baixar o arquivo. Ocorreram falhas durante o processamento do link.", True))
                
        threading.Thread(target=worker, daemon=True).start()

    #====================================================
    # DISPARO FLUXO POR LOTE - ARQUITETURA 6.1e
    #====================================================
    def disparar_download_lote(self):
        if not checar_executavel("yt-dlp"):
            ModalMensagem.show(self.root, "Configuração Necessária", "O motor 'yt-dlp' não está instalado!\nClique no botão 'CONFIGURAR' no topo direito para instalar automaticamente.", "erro")
            return
            
        if self.em_download_lote or self.em_download_manual:
            ModalMensagem.show(self.root, "Aguarde", "Já existe um processo em andamento!", "aviso")
            return
            
        itens_para_baixar = []
        for s in self.slots_lote:
            if s["ativo"].get():
                u = s["url"].get().replace('\n', '').replace('\r', '').strip()
                n = s["ent_nome"].get().replace('\n', '').replace('\r', '').strip()
                p = s["pasta"].get().replace('\n', '').replace('\r', '').strip()
                if u:
                    itens_para_baixar.append((s, p, n, u))
                    
        if not itens_para_baixar:
            ModalMensagem.show(self.root, "Lote Vazio", "Marque as caixas de seleção dos itens e informe os links para iniciar.", "aviso")
            return
            
        self.em_download_lote = True
        self.cancelado = False
        self.animando_conversao_lote = False
        self.lbl_overlay_lote.pack_forget()
        
        self.txt_log_l.delete("1.0", tk.END)
        self.sessao_log.clear()
        
        self.btn_download_lote.pack_forget()
        self.btn_limpar_lote_baixo.pack_forget()
        self.btn_cancelar_lote.pack(fill=tk.X, pady=12)
        
        # Bloqueia os botões LIMPAR nas trilhas e o botão principal inferior
        for s in self.slots_lote:
            s["btn_limpar"].config(state=tk.DISABLED)
        self.btn_limpar_lote_baixo.config(state=tk.DISABLED)
        
        def worker_lote():
            total = len(itens_para_baixar)
            self.progresso_lote = {item[0]["id"]: 0.0 for item in itens_para_baixar}
            resultados = {"erros": 0}
            
            for item in itens_para_baixar:
                self.root.after(0, lambda s=item[0]: s["set_visual"]("baixando"))
            
            def processar_item(slot, pasta, nome, url):
                id_s = slot["id"]
                self.root.after(0, lambda: slot["status"].set("Iniciando..."))
                self.root.after(0, lambda: slot["lbl_status"].config(fg=COR_AMARELO))
                
                try:
                    cmd_dur = [obter_comando("yt-dlp"), "--print", "duration_string", u]
                    eh_hotmart = "hotmart" in u.lower() or ".m3u8" in u.lower()
                    if eh_hotmart:
                        cmd_dur.extend(["--referer", "https://hotmart.com/", "--add-header", "Origin: https://hotmart.com"])
                    
                    proc_dur = subprocess.run(cmd_dur, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    dur_str = proc_dur.stdout.strip()
                    if dur_str:
                        self.root.after(0, lambda d=dur_str, sl=slot: sl["duracao"].set(f"Tempo total deste vídeo: {d}"))
                except Exception:
                    pass
                
                def cb_p(pct, det):
                    self.progresso_lote[id_s] = pct
                    prog_global = sum(self.progresso_lote.values()) / total
                    
                    if pct >= 90 and pct < 100:
                        self.root.after(0, lambda: self.bar_lote.configure(mode="indeterminate"))
                        self.root.after(0, lambda: self.bar_lote.start(15))
                        if not getattr(self, 'animando_conversao_lote', False):
                            self.animando_conversao_lote = True
                            self.root.after(0, self.animar_texto_conversao_lote)
                    else:
                        self.root.after(0, lambda: self.bar_lote.configure(mode="determinate", value=prog_global))
                        
                    nome_status = n if (n and n != PLACEHOLDER_NOME) else "Título Original"
                    
                    if "Aguardando Renderização" in det or "Unindo" in det or "Convertendo" in det or "Corrigindo" in det:
                        self.root.after(0, lambda: slot["status"].set("Processando..."))
                        self.root.after(0, lambda: self.var_prog_lote_txt.set(f"Item {id_s}/{total} ({nome_status}): {det}"))
                    else:
                        self.root.after(0, lambda: slot["status"].set(f"{det}"))
                        self.root.after(0, lambda: self.var_prog_lote_txt.set(f"Item {id_s}/{total} ({nome_status}): Baixando..."))
                        
                def cb_l(msg):
                    tag_msg = f"[Item {id_s:02d}] {msg}"
                    self.sessao_log.append(tag_msg)
                    self.root.after(0, lambda: self.txt_log_l.insert(tk.END, tag_msg + "\n"))
                    self.root.after(0, lambda: self.txt_log_l.see(tk.END))
                    
                ok, nome_baixado, ext_baixada, dur = self.executar_download_item(f"lote_{id_s}", pasta, nome, url, cb_progresso=cb_p, cb_log=cb_l, is_lote=True)
                
                if dur:
                    self.root.after(0, lambda d=dur, sl=slot: sl["duracao"].set(f"Tempo total deste vídeo: {d}"))
                
                if self.cancelado:
                    self.root.after(0, lambda: slot["status"].set("Cancelado"))
                    self.root.after(0, lambda: slot["lbl_status"].config(fg=COR_CINZA_TEXTO))
                    self.root.after(0, lambda: slot["set_visual"]("vazio"))
                    return

                if ok:
                    self.root.after(0, lambda: slot["status"].set("Concluído"))
                    self.root.after(0, lambda: slot["lbl_status"].config(fg=COR_VERDE_OK))
                    self.root.after(0, lambda: slot["url"].set(""))
                    self.root.after(0, lambda: slot["set_visual"]("concluido"))
                    self.root.after(0, lambda nb=nome_baixado, ext=ext_baixada: ToastNotification.show(self.root, "Item Concluído", f"{nb}.{ext} finalizado!"))
                else:
                    resultados["erros"] += 1
                    self.root.after(0, lambda: slot["status"].set("Erro"))
                    self.root.after(0, lambda: slot["lbl_status"].config(fg=COR_VERMELHO))
                    self.root.after(0, lambda: slot["set_visual"]("erro"))
            
            threads = []
            for item in itens_para_baixar:
                t = threading.Thread(target=processar_item, args=(item[0], item[1], item[2], item[3]))
                threads.append(t)
                t.start()
                
            for t in threads:
                t.join()
                
            self.em_download_lote = False
            self.animando_conversao_lote = False
            
            # Restaura botões
            for s in self.slots_lote:
                self.root.after(0, lambda btn=s["btn_limpar"]: btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_limpar_lote_baixo.config(state=tk.NORMAL))
            
            self.root.after(0, lambda: self.lbl_overlay_lote.pack_forget())
            self.root.after(0, lambda: self.bar_lote.stop())
            self.root.after(0, lambda: self.bar_lote.configure(mode="determinate"))
            
            self.root.after(0, lambda: self.btn_cancelar_lote.pack_forget())
            self.root.after(0, lambda: self.btn_download_lote.pack(fill=tk.X, pady=(15, 5)))
            self.root.after(0, lambda: self.btn_limpar_lote_baixo.pack(fill=tk.X))
            
            if self.cancelado:
                self.root.after(0, lambda: self.bar_lote.configure(value=0))
                self.root.after(0, lambda: self.var_prog_lote_txt.set("Processamento de Lote Cancelado pelo Usuário."))
                return

            self.root.after(0, lambda: self.bar_lote.configure(value=100))
            self.root.after(0, lambda: self.var_prog_lote_txt.set(f"Lote Finalizado! ({total} itens processados)"))
            
            total_b = total
            erros_b = resultados["erros"]
            if erros_b > 0:
                self.root.after(0, lambda t=total_b, e=erros_b: self.exibir_modal_finalizacao("Lote Finalizado com Ressalvas", f"O processamento do lote foi concluído, porém {e} iten(s) apresentaram falhas.", True))
            else:
                self.root.after(0, lambda t=total_b: self.exibir_modal_finalizacao("Lote Finalizado", f"O lote foi processado integralmente com sucesso! Todos os {t} itens foram baixados sem problemas.", False))
            
        threading.Thread(target=worker_lote, daemon=True).start()

#====================================================
# INICIALIZAÇÃO CONTROLADA COM IDENTIDADE DE PROCESSO DO WINDOWS
#====================================================
def iniciar_sistema():
    if os.name == 'nt':
        try:
            import ctypes
            app_id = 'sussuarana.down5.downloader.6.1e'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass
            
    root = tk.Tk()
    caminho_ico = obter_caminho_icone()
    try:
        if caminho_ico: root.iconbitmap(caminho_ico)
    except Exception: pass
        
    root.withdraw()
    
    def apos_splash():
        root.deiconify()
        root.lift()
        root.focus_force()
        app = DownloaderApp(root)
        
    splash = SplashScreen(root, apos_splash)
    root.mainloop()

if __name__ == "__main__":
    iniciar_sistema()