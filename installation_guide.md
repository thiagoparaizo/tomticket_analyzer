# Guia de Instalação para Desenvolvedores

Este guia contém instruções para configurar o ambiente de desenvolvimento e compilar a aplicação Analisador de Tickets de Suporte.

## Requisitos de Desenvolvimento
- Python 3.8 ou superior
- Bibliotecas Python conforme listadas em `requirements.txt`
- PyInstaller (para compilação do executável)

## Configuração do Ambiente de Desenvolvimento

### 1. Clone ou baixe os arquivos do projeto

### 2. Crie um ambiente virtual Python (recomendado)
```bash
python -m venv venv
```

### 3. Ative o ambiente virtual
- Windows:
```bash
venv\Scripts\activate
```
- Linux/macOS:
```bash
source venv/bin/activate
```

### 4. Instale as dependências
```bash
pip install -r requirements.txt
```

## Arquivo requirements.txt (se não existir)
Crie um arquivo `requirements.txt` com o seguinte conteúdo:

```
requests==2.30.0
pandas==2.0.1
PyQt5==5.15.9
PyInstaller==5.11.0
```

## Executando o Programa em Modo de Desenvolvimento
```bash
python ticket_analyzer.py
```

## Compilando o Executável com PyInstaller

### Usando o script de build
```bash
python build.py
```

### Compilação manual
```bash
pyinstaller ^
--name=TicketAnalyzer ^
--onefile ^
--windowed ^
--clean ^
--icon=icon.ico ^
--add-data="README.txt;." ^
--add-data="enhanced_classifier.py;." ^
--add-data="enhanced_results_tab.py;." ^
--hidden-import=pandas ^
--hidden-import=PyQt5 ^
--hidden-import=requests ^
--hidden-import=dateutil.parser ^
--collect-all PyQt5 ^
ticket_analyzer.py ticket_analyzer.py
```
#### Use ^como separador de linhas no Windows (CMD). Se você não estiver no Linux/macOS , troque ^por \.

O executável será gerado na pasta `dist/`.

## Estrutura de Arquivos
```
├── ticket_analyzer.py          # Arquivo principal do programa
├── enhanced_classifier.py      # Arquivo para reclassificação de interações
├── enhanced_results_tab.py     # Arquivo com aba de reclassificação aprimorada
├── build.py                    # Script para compilar o executável
├── requirements.txt            # Dependências do projeto
├── README.txt                  # Arquivo de ajuda (incluído no executável)
├── icon.ico                    # Ícone da aplicação
├── venv/                       # Ambiente virtual Python (não versionar)
├── build/                      # Pasta de build temporária (não versionar)
└── dist/                       # Executável compilado
```

## Recursos da API TomTicket
A aplicação utiliza os seguintes endpoints da API TomTicket:
- `https://api.tomticket.com/v2.0/ticket/list` - Para listar tickets
- `https://api.tomticket.com/v2.0/ticket/detail` - Para obter detalhes de um ticket

Consulte a documentação completa da API em: https://tomticket.tomticket.com/kb/chamados-api/consultar-chamados