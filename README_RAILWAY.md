# Contador de Pessoas por Foto - Preparado para Railway

Este pacote já está pronto para subir no Railway.

## Arquivos importantes

- `requirements.txt`: dependências para deploy.
- `Procfile`: comando de inicialização.
- `runtime.txt`: força Python 3.12.
- `railway.json`: configuração do Railway.
- `wsgi.py`: entrada do Gunicorn.
- `app/`: aplicação Flask.

## Como subir para o Railway

1. Crie uma conta em https://railway.app
2. Crie um novo projeto.
3. Escolha **Deploy from GitHub repo** ou envie este projeto para um repositório GitHub.
4. O Railway vai detectar Python/Nixpacks automaticamente.
5. Depois do deploy, abra **Settings > Networking** e gere um domínio público.
6. Acesse o domínio gerado.
7. Na tela do app, clique em **Mostrar QR Code**.
8. Leia o QR Code com o celular.

## Câmera do celular

No Railway o domínio vem com HTTPS real. Isso ajuda o navegador do celular a liberar a câmera.

Se a câmera ainda não abrir, use o campo **Selecionar/tirar foto pelo celular**. Esse modo funciona bem em praticamente todos os navegadores.

## Observação importante

O Railway usa armazenamento temporário. As imagens geradas em `app/results` podem sumir quando o serviço reiniciar. Para este app de contagem, isso não atrapalha o uso normal, pois as imagens são temporárias.

## Teste local antes do deploy

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Abra:

```text
http://127.0.0.1:5000
```
