import os
import PyInstaller.__main__
import shutil

# Garante que o diretório de build está limpo
if os.path.exists('./dist'):
    shutil.rmtree('./dist')
if os.path.exists('./build'):
    shutil.rmtree('./build')

print("Gerando executável com PyInstaller...")

# Configurações para o PyInstaller
PyInstaller.__main__.run([
    'ticket_analyzer.py',                   # Script principal
    '--name=TicketAnalyzer',               # Nome do executável
    '--onefile',                           # Um único arquivo executável
    '--windowed',                          # Aplicação com GUI (sem console)
    '--icon=icon.ico',                     # Ícone (comente se não tiver)
    '--add-data=README.txt;.',             # Arquivo de ajuda
    '--add-data=enhanced_classifier.py;.', # Módulo adicional
    '--add-data=enhanced_results_tab.py;.', # Módulo adicional
    '--clean',                             # Limpa cache
    # Bibliotecas necessárias
    '--hidden-import=pandas',
    '--hidden-import=PyQt5',
    '--hidden-import=requests',
    '--hidden-import=dateutil.parser',
    '--collect-all', 'PyQt5',              # Garante todos os recursos do PyQt5
    # Adicione aqui outros arquivos de configuração se necessário
    # '--add-data=config.ini;.',
])

print("Executável gerado com sucesso!")
print("Localização: ./dist/TicketAnalyzer.exe")