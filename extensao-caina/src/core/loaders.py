# encoding: utf-8
import json
from PyQt5.QtWidgets import *

def LoadJSON(filePath):
    try:
        with open(filePath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, ValueError):
        fileName = filePath.split('/')[-1]
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(f"Não foi possível abrir o arquivo {fileName}! Verifique se a instalação do programa foi realizada de maneira correta.")
        msg.exec_()
        return None
    return data
