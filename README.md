# Wasabi

这是 [Wasabi 的个人技术博客](https://sh1luo.github.io/)源代码，主要记录 Go 后端、系统原理、源码分析与工程实践。

## 本地运行

站点使用 Hugo Extended `0.165.0` 构建。安装对应版本后，统一通过 Makefile 执行常用操作：

```bash
make
```

不需要记住完整的 Hugo 或 Git 命令，`make` 会显示所有入口。日常写作只需要：

```bash
make new
make preview
make publish
```

`make new` 会询问文章文件名和分类，并创建一篇 `draft: true` 的草稿；`make preview` 默认包含草稿。写完后把文章头部的 `draft` 改为 `false`，再运行 `make publish`，它会检查站点、提交文章并推送到 `master`。

浏览器访问 <http://localhost:1313/>。生产构建、内部链接与页面锚点、图片备份完整性和工具回归检查：

```bash
make check
```

新增外部图片后，先执行 `make backup-images`，再检查、发布。外部图片仍由内容发布流程中的图床托管，可按需执行可用性巡检：

```bash
make check-external-images
```

可以通过 `HUGO` 指定 Hugo 二进制，例如 `make preview HUGO=/path/to/hugo`；`BIND` 和 `PORT` 可分别覆盖监听地址与端口。

### 外部图片备份与恢复

```bash
make backup-images
```

图片保存在 `backups/external-images/objects/`，`manifest.json` 记录原 URL、引用文章、备份文件、保存时间和 SHA-256。这个目录应随源码一起提交；它不进入网站发布目录。已验证的备份会直接复用，即使图床后来失效也不会被删除。下载失败会保留成功的备份和错误记录，并返回失败状态；再次运行会重试缺失或损坏的图片。

`make check` 和 CI 会离线校验备份，也会发现新文章中尚未备份的图片。恢复时，按原 URL 导出图片到一个尚不存在的文件：

```bash
python3 scripts/backup_external_images.py \
  --restore 'https://example.com/image.png' \
  --output static/images/restored.png
```

把示例 URL 换成清单中的原 URL。恢复后可重新上传到图床，或把 Markdown 图片链接改为 `/images/restored.png`。恢复命令会校验文件哈希并拒绝覆盖已有文件，全程无需联网。

`make publish` 会一起提交 `content/` 和 `backups/` 的变更，确保文章和图片副本同时保存。发布中的检查、暂存、提交或推送任何一步失败，命令都会停止并返回失败状态。

### 文章图片尺寸

站点会把文章图片默认限制在正文可读宽度内，不会修改图片 URL，也不影响同一份 Markdown 发布到其他平台。需要单独控制时，可以把尺寸写在 Markdown 图片标题中：

```markdown
![图片说明](https://example.com/image.jpg "size=small")
![图片说明](https://example.com/image.jpg "size=medium")
![图片说明](https://example.com/image.jpg "size=large")
![图片说明](https://example.com/image.jpg "size=full")
```

四档最大宽度分别约为 420、640、832 像素和正文全宽。这个写法仍是标准 Markdown；不了解该约定的平台只会忽略尺寸效果。若某个平台支持 HTML，也可以使用带 `width` 或内联 `style` 的 `<img>` 标签精确指定宽度。

### 从 Mac 访问开发机预览

先在开发机仓库中保持 `make preview` 运行，再在 Mac 建立隧道：

```bash
ssh -N -L 1313:127.0.0.1:1313 liujikun@10.37.126.33
```

隧道只负责转发连接；如果开发机没有运行 Hugo，浏览器会收到 `Connection refused`。

## 发布

`master` 分支更新后，[GitHub Actions](.github/workflows/hugo.yml) 会构建站点并发布到 GitHub Pages：

<https://sh1luo.github.io/>

Pull Request 会执行构建、内部链接检查、图片备份校验和工具回归测试，不发布线上版本。

## 目录

- `content/`：文章和栏目内容。
- `layouts/`：在 Hermit 主题之上的模板覆盖。
- `assets/`：站点自有并由 Hugo 指纹化的 CSS 与 JavaScript。
- `static/`：图标和站点自有图片。
- `themes/hermit/`：内置维护的 Hermit 主题副本，站点模板与脚本在根目录覆盖。
- `scripts/`：内部链接、锚点和外部图片检查。
- `backups/`：外部图片的可恢复副本和 URL 清单，不随网站发布。
- `tests/`：发布失败处理和图片备份、恢复的回归测试。

## 许可

文章与代码的许可范围见 [LICENSE.md](LICENSE.md)。

## 公众号

![公众号狗浪人儿二维码](static/images/wechat-qr.jpg)
