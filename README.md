# Chimpanzé (iPhone)

Script usado pelo atalho **Chimpanzé** do app Atalhos para baixar vídeos e áudios
(YouTube, Instagram, TikTok, X e outros) direto no iPhone, usando o app gratuito **a-Shell**.

## Instalar (no a-Shell)

```
curl -L -o ~/Documents/chimp.py https://raw.githubusercontent.com/johnmaacedo/chimpanze-ios/main/chimp.py
```

## Uso manual

```
python3 ~/Documents/chimp.py "https://..."   (mostra um menu)
python3 ~/Documents/chimp.py "Vídeo (máxima)" "https://..."
```

Opções: `Vídeo (máxima)`, `Vídeo 1080p`, `Vídeo 720p`, `Vídeo 480p`, `Só o áudio`, `Atualizar`.
