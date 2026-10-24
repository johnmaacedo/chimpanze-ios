# Chimpanzé Downloader para iPhone (roda dentro do app a-Shell)
# Uso: python3 ~/Documents/chimp.py "<opção>" "<link>"
# Opções: "Vídeo (máxima)", "Vídeo 1080p", "Vídeo 720p", "Vídeo 480p", "Atualizar"
import os
import re
import shutil
import subprocess
import sys

DOCS = os.path.expanduser("~/Documents")
PASTA = os.path.join(DOCS, "chimpanze_tmp")
SAIDAS = [d for d in {os.environ.get("SHORTCUTS"), DOCS} if d]


def voltar_para_atalhos():
    # Volta para o app Atalhos, que continua o atalho e salva o vídeo na galeria
    os.system("open shortcuts://")


def atualizar():
    print("Atualizando o motor de download...")
    subprocess.call([sys.executable, "-m", "pip", "install", "--user", "--upgrade",
                     "yt-dlp[default]", "yt-dlp-apple-webkit-jsi"])
    print("Pronto!")
    voltar_para_atalhos()


def codecs(arquivo):
    import json
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", arquivo],
                       capture_output=True, text=True)
    try:
        streams = json.loads(r.stdout).get("streams", [])
    except ValueError:
        streams = []
    v = next((s.get("codec_name", "") for s in streams if s.get("codec_type") == "video"), "")
    a = next((s.get("codec_name", "") for s in streams if s.get("codec_type") == "audio"), "")
    return v, a


def preparar_para_galeria(arquivo):
    """Deixa o MP4 no formato que a galeria aceita: HEVC marcado como hvc1 e áudio AAC."""
    v, a = codecs(arquivo)
    print(f"\nVídeo: {v or '?'} | Áudio: {a or 'sem áudio'}")
    if v not in ("h264", "hevc"):
        print("⚠️ Esse vídeo só existe num formato que a galeria do iPhone não aceita "
              f"({v}). Tente a opção 1080p.")
    saida = os.path.join(PASTA, "galeria.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", arquivo, "-map", "0:v:0", "-c:v", "copy"]
    if v == "hevc":
        cmd += ["-tag:v", "hvc1"]  # sem essa marca a galeria recusa vídeos HEVC (TikTok)
    if a:
        cmd += ["-map", "0:a:0"] + (["-c:a", "copy"] if a == "aac" else ["-c:a", "aac", "-b:a", "192k"])
    cmd += ["-movflags", "+faststart", saida]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(saida) and os.path.getsize(saida) > 0:
        return saida
    print("Aviso: não consegui ajustar o vídeo; salvando como veio.", (r.stderr or "")[-200:])
    return arquivo


def baixar(opcao, link):
    import yt_dlp

    texto = opcao.lower()
    audio = "udio" in texto
    m = re.search(r"(\d{3,4})p", texto)
    altura = int(m.group(1)) if m else None

    shutil.rmtree(PASTA, ignore_errors=True)
    os.makedirs(PASTA, exist_ok=True)
    opts = {
        "outtmpl": os.path.join(PASTA, "arquivo.%(ext)s"),
        "noplaylist": True,
        "retries": 5,
        "fragment_retries": 10,
    }
    if audio:
        # AAC (.m4a): toca no iPhone, no WhatsApp e em qualquer lugar
        opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "m4a"}]
        final = "chimpanze.m4a"
    else:
        h = f"[height<={altura}]" if altura else ""
        # A galeria do iPhone só aceita H.264 ou HEVC. VP9/AV1 (YouTube acima de 1080p) ela recusa.
        ok = "[vcodec~='^(avc|h264|hvc|hev|h265)']"
        opts["format"] = (f"bestvideo{ok}{h}+bestaudio[acodec^=mp4a]/"
                          f"bestvideo{ok}{h}+bestaudio/"
                          f"best{ok}{h}/"
                          f"bestvideo{h}+bestaudio/best{h}/best")
        opts["format_sort"] = ["res", "fps"]
        opts["merge_output_format"] = "mp4"
        final = "chimpanze.mp4"

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([link])

    gerados = [f for f in os.listdir(PASTA) if not f.endswith((".part", ".ytdl"))]
    if not gerados:
        raise RuntimeError("O download não gerou nenhum arquivo.")
    origem = os.path.join(PASTA, max(gerados, key=lambda f: os.path.getsize(os.path.join(PASTA, f))))
    if not audio:
        origem = preparar_para_galeria(origem)

    for d in SAIDAS:
        os.makedirs(d, exist_ok=True)
        for velho in ("chimpanze.mp4", "chimpanze.m4a"):
            try:
                os.remove(os.path.join(d, velho))
            except OSError:
                pass
        shutil.copyfile(origem, os.path.join(d, final))
    shutil.rmtree(PASTA, ignore_errors=True)

    print("\nPronto! Voltando para salvar na galeria...")
    voltar_para_atalhos()


MENU = ["Vídeo (máxima)", "Vídeo 1080p", "Vídeo 720p", "Vídeo 480p", "Atualizar o Chimpanzé"]


def perguntar():
    print("\n🐒 Chimpanzé — qual qualidade?\n")
    for i, item in enumerate(MENU, 1):
        print(f"  {i} - {item}")
    while True:
        try:
            n = int(input("\nDigite o número e aperte Enter: ").strip())
            if 1 <= n <= len(MENU):
                return MENU[n - 1]
        except (ValueError, EOFError):
            pass
        print("Número inválido.")


def main():
    if len(sys.argv) < 2:
        print('Uso: python3 ~/Documents/chimp.py "https://..."')
        return
    # Modo simples: só o link -> mostra o menu aqui mesmo
    if len(sys.argv) == 2 and re.search(r"https?://", sys.argv[1]):
        sys.argv = [sys.argv[0], perguntar(), sys.argv[1]]
    opcao = sys.argv[1]
    if "atualizar" in opcao.lower():
        atualizar()
        return
    if len(sys.argv) < 3 or not sys.argv[2].strip():
        print("Nenhum link recebido. Copie o link do vídeo e tente de novo.")
        return
    link = re.search(r"https?://\S+", sys.argv[2])
    if not link:
        print("Não encontrei um link válido em: " + sys.argv[2])
        return
    try:
        baixar(opcao, link.group(0))
    except Exception as e:  # noqa: BLE001
        print("\n❌ Não deu certo: " + str(e))
        print("Dica: tente a opção 'Atualizar' no atalho Chimpanzé e baixe de novo.")


if __name__ == "__main__":
    main()
