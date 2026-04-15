# 🏥 Guia de Compilação Local (Windows) - Pesagem Pro APAE

Este guia explica como gerar o executável `.exe` do sistema no seu próprio computador Windows.

## 1. Pré-requisitos

Você precisará instalar as seguintes ferramentas no seu Windows:

1.  **Python 3.10 ou superior:** [python.org](https://www.python.org/downloads/) (Marque a opção "Add Python to PATH" na instalação).
2.  **Git:** [git-scm.com](https://git-scm.com/downloads) (Para baixar o código).

---

## 2. Preparando o Ambiente

Abra o **Prompt de Comando (CMD)** ou **PowerShell** e execute os seguintes comandos:

```powershell
# 1. Instale o Flet e as bibliotecas de dados
pip install flet pandas openpyxl

# 2. Verifique se o Flet está funcionando
flet --version
```

---

## 3. Baixando o Código

No terminal, vá para a pasta onde deseja salvar o projeto e rode:

```powershell
git clone https://github.com/alexlambertini/pesagem-apae.git
cd pesagem-apae
```

---

## 4. Gerando o Executável (.exe)

Para criar o arquivo que você vai distribuir na clínica, rode o comando abaixo:

```powershell
flet build windows
```

### O que vai acontecer:
*   O Flet vai baixar o motor do Flutter (isso pode demorar uns 5-10 minutos na primeira vez).
*   Ele vai compilar o código Python para código nativo.
*   Uma pasta chamada `build\windows` será criada.
*   Lá dentro você encontrará o arquivo **`Pesagem Pro - APAE.exe`**.

---

## 📝 Notas Importantes

*   **Banco de Dados:** O banco de dados SQLite será criado automaticamente na pasta de usuário (`C:\Users\SEU_USUARIO\sistema_pesagem_apae.db`). Isso garante que os dados não sejam apagados se você atualizar o programa.
*   **Relatórios:** Os relatórios em Excel são salvos automaticamente na pasta **Documentos**.
*   **Sem Login:** O sistema abre direto na lista de pacientes conforme solicitado.

---
**Autor:** Alexandre Lambertini (via Gemini CLI)
