HUGO ?= hugo
HUGO_VERSION := 0.165.0
BIND ?= 127.0.0.1
PORT ?= 1313
HUGO_CACHEDIR ?= $(CURDIR)/.cache/hugo

.PHONY: help check-hugo preview build check check-external-images

help:
	@printf '%s\n' \
		'make preview               启动本地预览' \
		'make build                 生成生产站点' \
		'make check                 构建并检查内部链接与锚点' \
		'make check-external-images 检查外部图片可用性'

check-hugo:
	@command -v "$(HUGO)" >/dev/null || { printf '未找到 Hugo，请安装 Hugo Extended $(HUGO_VERSION)。\n' >&2; exit 1; }
	@"$(HUGO)" version | grep -q "v$(HUGO_VERSION)" || { printf '需要 Hugo Extended $(HUGO_VERSION)，当前版本：' >&2; "$(HUGO)" version >&2; exit 1; }
	@"$(HUGO)" version | grep -q extended || { printf '需要 Hugo Extended 版本。\n' >&2; exit 1; }

preview: check-hugo
	"$(HUGO)" server --cacheDir "$(HUGO_CACHEDIR)" --bind "$(BIND)" --port "$(PORT)" --disableFastRender --noHTTPCache

build: check-hugo
	"$(HUGO)" --cacheDir "$(HUGO_CACHEDIR)" --gc --minify --printPathWarnings

check: build
	python3 scripts/check_internal_links.py public

check-external-images:
	python3 scripts/check_external_images.py content
