# dotfiles

WSL2（Ubuntu）+ Windows の Alacritty で使っている設定。

| ディレクトリ | 置き場所 | 方式 |
| --- | --- | --- |
| `starship/starship.toml` | `~/.config/starship.toml` | リンク |
| `starship/themes/` | `~/.config/starship/themes/` | リンク |
| `mise/config.toml`, `miserc.toml` | `~/.config/mise/` | リンク |
| `claude/settings.json`, `statusline.py` | `~/.claude/` | リンク |
| `claude/skills/grilling/` | `~/.claude/skills/grilling` | リンク |
| `alacritty/alacritty.toml` | `%APPDATA%\alacritty\alacritty.toml` | コピー |

## 使い方

```bash
git clone https://github.com/virtual-hippo/dotfiles.git ~/dotfiles
~/dotfiles/install.sh
```

- 既存のファイルは `<path>.bak.YYYYMMDD` に退避してから置き換える。何度実行してもよい。
- Alacritty の設定はコピーなので、Windows 側で直したら `alacritty/alacritty.toml` へ書き戻す。

## 前提

- フォント: [UDEV Gothic](https://github.com/yuru7/udev-gothic) の `UDEV Gothic 35NFLG`（Nerd Font 入り）を Windows に入れる。Starship と statusline のアイコンに使う。
- mise: `curl https://mise.run | sh` で入れ、`mise install` で starship / node / pnpm / aws-cli などを入れる。
- Claude Code: `settings.json` の SessionStart フックは herdr の `~/.claude/hooks/herdr-agent-state.sh` を呼ぶ。herdr が入れるファイルなのでこのリポジトリには含めない。herdr を使わない環境では `hooks` を消す。
- `statusline.py` は python3 を使う。
- `claude/skills/grilling/` は [mattpocock/skills](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling)（MIT、4ae2317）の写し。更新するときは `SKILL.md` を取り直す。

## .bashrc に追記するもの

`.bashrc` はマシンごとに違うので管理しない。以下を `mise activate` → `starship init` の順で追記する。

```bash
# Claude Code（WSL から Windows 側のプロファイルを見に行かせない）
export CLAUDE_CODE_SKIP_WINDOWS_PROFILE=1
export USERPROFILE="/mnt/c/Users/<Windows のユーザー名>"

# bracketed paste を無効にする
bind 'set enable-bracketed-paste off'

# mise などの置き場所
export PATH="$HOME/.local/bin:$PATH"

# mise
eval "$(~/.local/bin/mise activate bash)"

# starship（mise で管理。mise activate の後に置く）
export STARSHIP_LOG=error  # /mnt/c などでのスキャン遅延の警告を出さない
eval "$(starship init bash)"

# Starship のテーマをこのシェルだけで試す: starship-theme <名前> / 引数なしで一覧 / reset で元に戻す
starship-theme() {
  local d=~/.config/starship/themes
  if [[ -z $1 ]]; then ls "$d" | sed 's/\.toml$//'; return; fi
  if [[ $1 == reset ]]; then unset STARSHIP_CONFIG; return; fi
  [[ -f $d/$1.toml ]] || { echo "テーマがありません: $1" >&2; return 1; }
  export STARSHIP_CONFIG=$d/$1.toml
}
_starship_theme_complete() { COMPREPLY=($(compgen -W "reset $(ls ~/.config/starship/themes | sed 's/\.toml$//')" -- "${COMP_WORDS[1]}")); }
complete -F _starship_theme_complete starship-theme

# シークレットやマシン固有の設定は ~/.bashrc.local に書く（Git に入れない）
[ -f ~/.bashrc.local ] && . ~/.bashrc.local
```
