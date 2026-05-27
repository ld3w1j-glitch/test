# Contador de Pessoas em Tempo Real - Flask + OpenCV

Este projeto permite abrir a câmera do celular pelo navegador e contar pessoas em tempo quase real.

## Funções

- Login simples
- QR Code para abrir no celular
- Câmera ao vivo no navegador
- Contagem contínua por frames
- Botão para iniciar/parar leitura
- Upload de foto manual
- Histórico de leituras
- Correção manual da quantidade
- Exportação CSV
- Relatório PDF simples
- Pronto para Railway

## Login padrão

Usuário: `admin`  
Senha: `admin`

No Railway, configure:

```txt
APP_USER=seu_usuario
APP_PASSWORD=sua_senha
SECRET_KEY=uma_chave_grande
PUBLIC_URL=https://seu-dominio.up.railway.app
```

## Rodar no Windows local

Instale Python 3.12.

Depois execute:

```bat
INSTALAR_WINDOWS.bat
iniciar_http.bat
```

Para câmera no celular local, geralmente precisa HTTPS:

```bat
iniciar_https_camera.bat
```

O navegador pode mostrar "site não seguro" porque o certificado é local.

## Subir no Railway

1. Crie projeto no Railway.
2. Suba este ZIP ou conecte o GitHub.
3. Gere domínio em Settings > Networking.
4. Configure as variáveis de ambiente.
5. Acesse `/qr` para abrir o QR Code.

## Observação sobre precisão

Esta versão leve usa OpenCV HOG para detectar pessoas e Haar Cascade para rosto como apoio.
Ela funciona melhor com boa iluminação, pessoas visíveis e câmera estável.

Para maior precisão, existe o arquivo `requirements_yolo_opcional.txt`.
YOLO é mais pesado e pode exigir servidor com mais memória.