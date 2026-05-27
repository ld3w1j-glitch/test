# Contador por Foto - Flask + OpenCV

Aplicativo web para contar objetos em uma foto usando Python, Flask e OpenCV.

## O que ele faz

- Abre uma página web pelo navegador.
- Permite enviar foto ou capturar pela câmera.
- Processa a imagem com OpenCV.
- Conta objetos separados usando contornos.
- Mostra a imagem marcada com número em cada item.
- Mostra a máscara usada na leitura.
- Permite ajustar sensibilidade, área mínima, área máxima, suavização e tipo de contraste.

## Limitação importante

Este app usa contagem por contraste/contorno. Ele funciona melhor quando:

- os objetos estão separados;
- existe contraste entre objeto e fundo;
- a foto está bem iluminada;
- não existem sombras fortes;
- os itens não estão empilhados ou grudados.

Para contar objetos grudados, frutas empilhadas, pães muito próximos, parafusos amontoados etc., o ideal é treinar um modelo de IA, como YOLO, com fotos reais dos seus itens.

## Instalação no Windows

1. Instale Python 3.12.
2. Marque a opção `Add python.exe to PATH`.
3. Extraia este ZIP.
4. Abra a pasta do projeto.
5. Clique duas vezes em:

```bat
INSTALAR_WINDOWS.bat
```


## Novo: QR Code automático ao iniciar

Agora, quando você clicar em `iniciar_http.bat` ou `iniciar_https_camera.bat`, o programa abre automaticamente no computador uma tela com QR Code.

Basta apontar a câmera do celular para o QR Code e abrir o link. O celular precisa estar na mesma rede Wi-Fi do computador.

Também existe um botão na tela principal chamado `Mostrar QR Code`.

## Rodar no computador

Depois da instalação, clique em:

```bat
iniciar_http.bat
```

Abra no navegador:

```text
http://127.0.0.1:5000
```

## Acessar pelo celular na mesma internet

1. Descubra o IP do computador no Windows:

```bat
ipconfig
```

Procure o `Endereço IPv4`, por exemplo:

```text
192.168.0.10
```

2. No celular, conectado no mesmo Wi-Fi, abra:

```text
http://192.168.0.10:5000
```

## Sobre câmera do celular

Navegadores modernos normalmente exigem HTTPS para liberar a câmera quando você acessa por outro dispositivo da rede.

Por isso existem duas opções:

### Opção 1: usar upload/tirar foto pelo campo de arquivo

Funciona mesmo em HTTP. No celular, clique em `Selecionar/tirar foto pelo celular`.

### Opção 2: usar câmera ao vivo com HTTPS local

Clique em:

```bat
iniciar_https_camera.bat
```

Depois acesse pelo celular:

```text
https://SEU-IP:5443
```

O navegador pode mostrar aviso de certificado, porque é um certificado temporário local. Avance somente se estiver na sua própria rede.

## Como melhorar a precisão

- Use fundo branco para objetos escuros.
- Use fundo preto para objetos claros.
- Espalhe os objetos sem encostar.
- Evite sombra.
- Tire a foto de cima.
- Ajuste `Área mínima` para remover sujeira/ruído.
- Diminua `Área mínima` se objetos pequenos não forem contados.
- Use `Misturado / iluminação irregular` quando a luz estiver ruim.

## Arquivos principais

```text
run.py                         Servidor HTTP
run_https.py                   Servidor HTTPS local
app/routes.py                  Rotas Flask e processamento OpenCV
app/templates/index.html       Tela principal
app/static/css/style.css       Estilo visual
app/static/js/app.js           Câmera, upload e envio da imagem
requirements.txt               Dependências
```

---

## Deploy no Railway

Este ZIP também contém preparação para Railway:

- `Procfile`
- `railway.json`
- `runtime.txt`
- `wsgi.py`
- `README_RAILWAY.md`

No Railway, use o domínio HTTPS gerado pela plataforma e clique em **Mostrar QR Code** para abrir pelo celular.
