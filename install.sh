#!/usr/bin/env bash
# dotfiles の設定を所定の場所へ置く。何度実行してもよい。
# - WSL 側: シンボリックリンクを張る
# - Alacritty（Windows 側）: コピーする（Windows から WSL 内へのリンクは使わない）
# 既存のファイルは <path>.bak.YYYYMMDD[-N] に退避する。
set -euo pipefail

DOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TODAY="$(date +%Y%m%d)"

backup() {
  local p="$1" b="$1.bak.$TODAY" n=2
  while [[ -e $b ]]; do b="$1.bak.$TODAY-$n"; n=$((n + 1)); done
  mv "$p" "$b"
  echo "  退避: $p -> $b"
}

link() {
  local src="$DOT/$1" dst="$2"
  if [[ -L $dst && "$(readlink "$dst")" == "$src" ]]; then
    echo "ok    $dst"; return
  fi
  mkdir -p "$(dirname "$dst")"
  if [[ -e $dst || -L $dst ]]; then backup "$dst"; fi
  ln -s "$src" "$dst"
  echo "link  $dst -> $src"
}

link starship/starship.toml   ~/.config/starship.toml
link starship/themes          ~/.config/starship/themes
link mise/config.toml         ~/.config/mise/config.toml
link mise/miserc.toml         ~/.config/mise/miserc.toml
link claude/settings.json     ~/.claude/settings.json
link claude/statusline.py     ~/.claude/statusline.py
link claude/skills/grilling   ~/.claude/skills/grilling

# Alacritty（Windows 側の %APPDATA%\alacritty\alacritty.toml）
if command -v cmd.exe >/dev/null 2>&1; then
  appdata="$(cmd.exe /c 'echo %APPDATA%' 2>/dev/null | tr -d '\r')"
  dst="$(wslpath "$appdata")/alacritty/alacritty.toml"
  if [[ -f $dst ]] && cmp -s "$DOT/alacritty/alacritty.toml" "$dst"; then
    echo "ok    $dst"
  else
    mkdir -p "$(dirname "$dst")"
    if [[ -e $dst ]]; then backup "$dst"; fi
    cp "$DOT/alacritty/alacritty.toml" "$dst"
    echo "copy  $dst"
  fi
else
  echo "skip  Alacritty（WSL ではないため）"
fi
