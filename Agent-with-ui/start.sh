#!/bin/bash

tilix \
  -e "mongod --dbpath ~/mongodb-data" \
  -e "cd ~/RAG/Agent-with-ui/Agent-be && source ./../../venv/bin/activate && npm run dev" \
  -e "cd ~/RAG/Agent-with-ui/Agent-be/src && source ./../../../venv/bin/activate && python3 py_server.py" \
  -e "cd ~/RAG/Agent-with-ui/Agent-fe && npm run dev" \
  -e "cd ~/Downloads/Postman && ./Postman"
