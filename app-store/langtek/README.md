Pyenv Custom Python Version:
============================
# Python 3.13 to avoid dependency conflicts with coloqui and other libraries

# First install system dependencies required for pyenv:
# Ubuntu/Debian:
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncurses5-dev libncursesw5-dev xz-utils tk-dev \
libffi-dev liblzma-dev python3-openssl git

# Install pyenv:
curl https://pyenv.run | bash

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init - bash)"' >> ~/.bashrc
source ~/.bashrc

# Install and set Python 3.13:
pyenv install 3.12
cd /home/adminotaur/Documents/git/flet/langtek
pyenv local 3.12.11

# To unisntall
pyenv uninstall 3.12

Flet using poetry:
==================
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -
poetry --version
cd /home/adminotaur/Documents/git/langtek
poetry init --no-interaction --python=">=3.9"
poetry add "flet[all]"
poetry run flet create
# Make sure to update your dependencies in the pyproject.toml
poetry env use $(pyenv which python)
poetry lock && poetry install
poetry run flet run src/main.py
flet build apk -v
flet build linux -v
# Optional: If you wish to uninstall: 
curl -sSL https://install.python-poetry.org | python3 - --uninstall
* References:
    - poetry - handles venv automatically. https://python-poetry.org/

# Linux audio requires
sudo apt install libmpv2
sudo ln -s /usr/lib/x86_64-linux-gnu/libmpv.so.2 /usr/lib/x86_64-linux-gnu/libmpv.so.1



LangTek:
========
AI. Can you help? I currently have a project in flutter that I need to migrate to Flet. lets as of now try to do a one for one migration. Meanin we should try to presever the code and logic the best we can. We can also sue an equivalent library in Python to help if needed. For example try to find an equvalent library from flutter to python if need be and if you can not find the same library then use one that is simlar. As long as the UI features look the same . The word for word trasnaltor logic and the contextual optional translator , etc. 

Experiemntal: CAUTION AI, PLEASE DO NOT DO THIS PART YET:
=========================================================
Lets try to first get the conversion done from flutter to python FLET. Then we can later work on this part , as of now please stop here and do not try this research. 

Translator:
----------
* Argos Offline trasnaltor - If I can utilize to trasnlate word for word and contextual , maybe all I need. 
* C
* I need to test the speed and amount of storage this uses. 
* If not practical, can still utlize argos or libre trasnalte to help build my DB to be better. 
* Can also make sure simply transalte utilizes these libre trasnlate correctly as well. 
* Objectbox - Potential offline storage. ?

TTS:
---
# Test TTS. Maybe just use google tts like I currently am if these do not work right. 
* https://pypi.org/project/f5-tts/ ( Says I need to reference seech audio?)
* https://pypi.org/project/e2-tts-pytorch/
* Seed-TTS - https://github.com/BytedanceSpeech/seed-tts-eval?tab=readme-ov-file
* Mozilla TTS
* https://pypi.org/project/pyttsx3/
* https://pypi.org/project/pyttslib/

Security:
---------
* Pyarmour
* LocalPCP
* APK Hunt/Scan
* Subscriptions - Google Play Billing Library + Local PCP . If no subscription , PCP can lock the app. Make sure works offline  
  too. App Validity. 
* References:
    - https://wiki.python.org/moin/Pyarmor
    - https://github.com/alphabetanetcom/local-python-code-protector



# Example
import flet as ft

def main(page: ft.Page):
    page.title = "Flet counter example"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)

    def minus_click(e):
        txt_number.value = str(int(txt_number.value) - 1)
        page.update()

    def plus_click(e):
        txt_number.value = str(int(txt_number.value) + 1)
        page.update()

    page.add(
        ft.Row(
            [
                ft.IconButton(ft.Icons.REMOVE, on_click=minus_click),
                txt_number,
                ft.IconButton(ft.Icons.ADD, on_click=plus_click),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

ft.app(main)