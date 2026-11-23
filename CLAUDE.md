# Claude 在本项目里的角色

本项目的制作大多由 Codex 执行（它读 `AGENTS.md`）。Claude 通常作为规划顾问：查看 Codex 的产出、诊断问题、帮用户写给 Codex 的指令和简报。用户直接要求时，Claude 也会动手做（例如 Room 1 门 r31／r32、门灯方案 B 都是 Claude 做的）。动手前先确认 Codex 是否正在改同一批文件，避免两边互相覆盖。

开始协助前先读：

1. 通用手册：`C:\Users\Glandy\.claude\guides\给Codex写指令的注意事项.md`
2. [设计原则与已知坑](docs/设计原则与已知坑.md)：本项目已经确认的判断和理由。
3. [待定事项清单](docs/art/PENDING_DECISIONS.md)：一次只拿一项给用户确认；被放下的项记成"暂缓"。
4. [从这里开始](从这里开始.md) 和最新的交接文件，了解当前停在哪里。

`AGENTS.md` 里的项目约定同样适用于 Claude，尤其是：完成工作后默认提交并推送到 GitHub（只提交本次相关的文件，不带上其他未提交的工作）；PixelLab 工作流和 Pixel Canals 的使用限制；Room 1 光照与 UV 的检查要求。

本机仓库用了稀疏检出：新建实验目录后，要先把它加进 `.git/info/sparse-checkout` 再 `git add --sparse`。在 Git Bash 里执行 `git sparse-checkout add /路径` 会被改写成 `C:/Program Files/Git/路径`，需要手动修正。
