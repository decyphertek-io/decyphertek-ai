#!/bin/bash
sudo apt update && sudo apt install -y gh
gh auth login
gh workflow list
cd /home/adminotaur/Documents/git/flet/decyphertek-ai/mobile-app/custom
gh workflow run decyphertek-ai.yml --ref main
gh run list --workflow=decyphertek-ai.yml