Flet using poetry:
==================
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -
poetry --version
cd /home/adminotaur/Documents/git/langtek
poetry init --no-interaction --python=">=3.10"
poetry add "flet[all]"
poetry run flet create
# Make sure to update your dependencies in the pyproject.toml
poetry lock && poetry install
poetry run flet run src/main.py
flet build apk -v
flet build linux -v
# Optional: If you wish to uninstall: 
curl -sSL https://install.python-poetry.org | python3 - --uninstall
* References:
    - poetry - handles venv automatically. https://python-poetry.org/

Ansible APP:
============
This app provides a graphical interface for Ansible, Nmap, and bash operations using Flet. Try to keep it minimal and focused. Key features include:

Pure Python Implementation:
---------------------------
Except for the terminal relay (using pty), the app is entirely in Python. The PTY python library essentailly mirrors the linux terminal. This is useful if you need to run linux commands. 

Ansible Playbook Execution: 
---------------------------
Run Ansible playbooks directly from the app.
- Schedule playbooks. 
- AWX type UI . 

Nmap Network Scanning: 
----------------------
Discover hosts and services on your network.
- Good to map a network and create a ansible host config and to troubleshoot netwrok access. 

Network Mapping Integration: 
----------------------------
Combine Nmap results with Ansible to automate device management.

Terminal Relay: 
---------------
Interact with the terminal within the app for advanced operations.
- Allows using bash script to run anything from packer, terraform, and python.
- This bundles nicely so I dont have to add a bunch of features. Linux only. ( Maybe Powershell option? )

Integrate Cloud access libraries:
---------------------------------
Enable access to Google , Amazon , and Microsoft Cloud via Python libraries. 

Optional SKIP : ( Wait to implement , build everything else first , skip for now dumfuck-ai !!! AI Integration:) 
-------------------------
A lightweight coding model is integrated to assist with:
- Generating Ansible playbooks from natural language descriptions.

