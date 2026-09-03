HUGO ?= hugo
HUGO_VERSION := 0.165.0
BIND ?= 127.0.0.1
PORT ?= 1313
HUGO_CACHEDIR ?= $(CURDIR)/.cache/hugo
NAME ?=
SECTION ?=
MESSAGE ?=

.DEFAULT_GOAL := help

.PHONY: help check-hugo new preview build check check-external-images publish

help:
	@printf '%s\n' \
		'make new                   交互式创建一篇草稿' \
		'make preview               启动本地预览（包含草稿）' \
		'make build                 生成生产站点' \
		'make check                 构建并检查内部链接与锚点' \
		'make check-external-images 检查外部图片可用性' \
		'make publish               检查、提交并推送文章' \
		'' \
		'只需要记住 make；它会显示这份帮助。'

check-hugo:
	@command -v "$(HUGO)" >/dev/null || { printf '未找到 Hugo，请安装 Hugo Extended $(HUGO_VERSION)。\n' >&2; exit 1; }
	@"$(HUGO)" version | grep -q "v$(HUGO_VERSION)" || { printf '需要 Hugo Extended $(HUGO_VERSION)，当前版本：' >&2; "$(HUGO)" version >&2; exit 1; }
	@"$(HUGO)" version | grep -q extended || { printf '需要 Hugo Extended 版本。\n' >&2; exit 1; }

new: check-hugo
	@name='$(NAME)'; \
	if [ -z "$$name" ]; then \
		printf '文章文件名（例如 go-memory-model）: '; \
		IFS= read -r name; \
	fi; \
	if [ -z "$$name" ]; then \
		printf '文章文件名不能为空。\n' >&2; \
		exit 1; \
	fi; \
	case "$$name" in \
		/*|*/*|*..*) printf '文件名不能包含路径或 ..。\n' >&2; exit 1 ;; \
	esac; \
	name=$$(printf '%s' "$$name" | tr ' ' '-'); \
	name=$${name%.md}; \
	section='$(SECTION)'; \
	if [ -z "$$section" ]; then \
		printf '分类（留空为普通文章，例如 go、chore）: '; \
		IFS= read -r section; \
	fi; \
	case "$$section" in \
		/*|*..*|*' '*) printf '分类格式不正确。\n' >&2; exit 1 ;; \
	esac; \
	if [ -n "$$section" ]; then \
		target="posts/$$section/$$name.md"; \
	else \
		target="posts/$$name.md"; \
	fi; \
	"$(HUGO)" new content -k posts "$$target"; \
	printf '\n已创建 content/%s\n运行 make preview 即可预览草稿。\n' "$$target"

preview: check-hugo
	"$(HUGO)" server --cacheDir "$(HUGO_CACHEDIR)" --bind "$(BIND)" --port "$(PORT)" --buildDrafts --disableFastRender --noHTTPCache

build: check-hugo
	"$(HUGO)" --cacheDir "$(HUGO_CACHEDIR)" --gc --minify --printPathWarnings

check: build
	python3 scripts/check_internal_links.py public

check-external-images:
	python3 scripts/check_external_images.py content

publish: check
	@branch=$$(git branch --show-current); \
	if [ "$$branch" != 'master' ]; then \
		printf '当前分支是 %s；只有 master 会自动部署。\n' "$$branch" >&2; \
		exit 1; \
	fi; \
	git add content; \
	drafts=$$(git diff --cached --name-only --diff-filter=ACM -- content | while IFS= read -r file; do \
		if grep -q '^draft:[[:space:]]*true[[:space:]]*$$' "$$file"; then printf '%s\n' "$$file"; fi; \
	done); \
	if [ -n "$$drafts" ]; then \
		printf '以下文章仍是草稿，请先把 draft 改为 false：\n%s\n' "$$drafts" >&2; \
		exit 1; \
	fi; \
	if git diff --cached --quiet -- content; then \
		printf 'content/ 下没有需要发布的改动。\n' >&2; \
		exit 1; \
	fi; \
	message='$(MESSAGE)'; \
	if [ -z "$$message" ]; then \
		printf '提交说明（留空使用默认值）: '; \
		IFS= read -r message; \
	fi; \
	if [ -z "$$message" ]; then message='post: publish article'; fi; \
	git commit -m "$$message" -- content; \
	git push origin "$$branch"
