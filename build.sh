#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala o Rust caso alguma dependência (como pydantic-core, bcrypt ou tokenizers) precise compilar do código-fonte
curl https://sh.rustup.rs -sSf | sh -s -- -y
export PATH="$HOME/.cargo/bin:$PATH"

pip install --upgrade pip
pip install -r requirements.txt

git add build.sh
git commit -m "Fix cargo/rust dependency for Render"
git push
