# Chimpanzé Downloader para iPhone (roda dentro do app a-Shell)
# Uso: python3 ~/Documents/chimp.py "<link ou texto com o link>"
#      python3 ~/Documents/chimp.py atualizar
# Baixa sempre na melhor qualidade que a galeria do iPhone aceita e volta para o Atalhos.
import json
import os
import re
import shutil
import subprocess
import sys

DOCS = os.path.expanduser("~/Documents")
PASTA = os.path.join(DOCS, "chimpanze_tmp")
SAIDAS = [d for d in {os.environ.get("SHORTCUTS"), DOCS} if d]
FINAL = "chimpanze.mp4"
# Codecs que a galeria do iPhone aceita
COMPAT = "[vcodec~='^(avc|h264|hvc|hev|h265|bytevc1)']"


APPS = {  # para voltar ao app de onde o vídeo veio
    "instagram.com": "instagram://", "instagr.am": "instagram://",
    "tiktok.com": "tiktok://", "youtube.com": "youtube://", "youtu.be": "youtube://",
    "x.com": "twitter://", "twitter.com": "twitter://", "facebook.com": "fb://",
    "fb.watch": "fb://", "reddit.com": "reddit://",
}


def salvar_na_galeria(link):
    """Chama o atalho 'Chimp Video' (salva na galeria) e depois volta para o app de origem."""
    from urllib.parse import quote
    url = "shortcuts://x-callback-url/run-shortcut?name=Chimp%20Video"
    volta = next((v for k, v in APPS.items() if k in link.lower()), "")
    if volta:
        url += "&x-success=" + quote(volta, safe="")
    os.system(f'open "{url}"')


def atualizar():
    print("Atualizando o motor de download...")
    subprocess.call([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "--quiet",
                     "yt-dlp[default]", "yt-dlp-apple-webkit-jsi"])


def apagar_saidas():
    for d in SAIDAS:
        try:
            os.remove(os.path.join(d, FINAL))
        except OSError:
            pass


def codecs(arquivo):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", arquivo],
                       capture_output=True, text=True)
    try:
        streams = json.loads(r.stdout).get("streams", [])
    except ValueError:
        streams = []
    v = next((s.get("codec_name", "") for s in streams if s.get("codec_type") == "video"), "")
    a = next((s.get("codec_name", "") for s in streams if s.get("codec_type") == "audio"), "")
    return v, a


def ffmpeg(args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + args, capture_output=True, text=True)
    return r.returncode == 0


def preparar_para_galeria(arquivo):
    """MP4 que a galeria aceita: H.264 ou HEVC (marcado hvc1) e áudio AAC."""
    v, a = codecs(arquivo)
    print(f"Formato baixado: vídeo {v or '?'} / áudio {a or 'nenhum'}")
    saida = os.path.join(PASTA, "galeria.mp4")
    audio = (["-map", "0:a:0", "-c:a", "copy"] if a == "aac" else
             ["-map", "0:a:0", "-c:a", "aac", "-b:a", "192k"] if a else [])

    if v in ("h264", "hevc"):
        tag = ["-tag:v", "hvc1"] if v == "hevc" else []
        if ffmpeg(["-i", arquivo, "-map", "0:v:0", "-c:v", "copy"] + tag + audio +
                  ["-movflags", "+faststart", saida]):
            return saida
    else:
        # Formato que a galeria recusa (VP9/AV1): converte para H.264 no chip do iPhone
        print("Convertendo para um formato que a galeria aceita...")
        if ffmpeg(["-i", arquivo, "-map", "0:v:0", "-c:v", "h264_videotoolbox", "-b:v", "12M",
                   "-pix_fmt", "yuv420p"] + audio + ["-movflags", "+faststart", saida]):
            return saida
    print("Aviso: não consegui ajustar o formato; vou salvar como veio.")
    return arquivo


def baixar(link):
    import yt_dlp

    shutil.rmtree(PASTA, ignore_errors=True)
    os.makedirs(PASTA, exist_ok=True)
    opts = {
        "outtmpl": os.path.join(PASTA, "arquivo.%(ext)s"),
        "noplaylist": True,
        "retries": 5,
        "fragment_retries": 10,
        # Melhor vídeo em formato compatível; se não houver, o melhor que existir (e converte depois)
        "format": (f"bestvideo{COMPAT}+bestaudio[acodec^=mp4a]/bestvideo{COMPAT}+bestaudio/"
                   f"best{COMPAT}/bestvideo+bestaudio/best"),
        "format_sort": ["res", "fps"],
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([link])

    gerados = [f for f in os.listdir(PASTA) if not f.endswith((".part", ".ytdl"))]
    if not gerados:
        raise RuntimeError("O download não gerou nenhum arquivo.")
    origem = os.path.join(PASTA, max(gerados, key=lambda f: os.path.getsize(os.path.join(PASTA, f))))
    origem = preparar_para_galeria(origem)
    for d in SAIDAS:
        os.makedirs(d, exist_ok=True)
        shutil.copyfile(origem, os.path.join(d, FINAL))
    shutil.rmtree(PASTA, ignore_errors=True)


def main():
    texto = " ".join(sys.argv[1:]).strip()
    if texto.lower() == "atualizar":
        atualizar()
        print("Pronto!")
        return
    m = re.search(r"https?://[^\s\"'<>]+", texto)
    if not m:
        print("Não encontrei um link. Copie o link do vídeo (ou use Compartilhar) e tente de novo.")
        print("Recebido: " + (texto or "(nada)"))
        return
    link = m.group(0)
    print("🐒 Baixando: " + link + "\n")
    apagar_saidas()
    try:
        baixar(link)
    except Exception as e1:  # noqa: BLE001
        # As redes mudam com frequência: atualiza o motor e tenta mais uma vez
        print("\nPrimeira tentativa falhou (" + str(e1)[:200] + "). Atualizando e tentando de novo...")
        atualizar()
        try:
            baixar(link)
        except Exception as e2:  # noqa: BLE001
            apagar_saidas()
            print("\n❌ NÃO DEU CERTO: " + str(e2))
            print("\n👉 Tire um print desta tela e mande para o Claude.")
            return
    print("\n✅ Pronto! Salvando na galeria...")
    salvar_na_galeria(link)


if __name__ == "__main__":
    main()
