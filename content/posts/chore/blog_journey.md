---
title: "几经周折的博客变迁史"
date: 2021-01-06 21:13:13
toc: true
tags:
  - 博客
  - CDN
  - 杂谈
---

仔细想起来我的博客旅程也有好多年了，兜兜转转地走了不少弯路，也确实在这个过程中学到了很多东西，大致有这些时间节点：

1. 尝试购买了国内域名和学生机服务器，看到自己写的内容能在公网上让全世界的人看到就高兴了好久，内容很随意，自己管理。
2. 使用 [Hexo](https://github.com/hexojs/hexo) 框架系统化内容，并部署在 GitHub Pages 交给 GitHub 管理。
3. 转用 [Hugo](https://github.com/gohugoio/hugo) 框架，利用 GitHub Actions 自动化构建，依然在 GitHub Pages。

![现在的博客](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/image-20210118174633253.png)

前前后后也折腾了好几年，技术上的提升我倒觉得不太大，因为折腾的挺多但是都是应用层面上的，对我来说更多的是 **动手能力** 的提高，有好多东西不经过自己亲手尝试是根本理解不了的，我前面很多东西就是别人远程或者一步一步告诉我让我去点这个点那个就可以了，但是回过头来问你，你根本不知道发生了什么，甚至隔天就忘，这是典型的不理解、死记硬背式学习方法。

我之所以最终选择将博客托管在 GitHub Pages，也是考虑都未来可能自己不会坚持购买服务器，说不定哪天没有服务器但是还写博客，那样就没地方在线看了。

最终采用的方案是：Hugo + GitHub Actions + GitHub Pages + 自定义域名。最终的效果是，只需要本地编写博客文件后，直接推送即可自动化构建 + 自动更新推送。

唯一的缺点是我的域名是在国外的平台 [Namesilo](https://www.namesilo.com/) 购买的，无法使用 CDN 加速，导致国内用户时常访问异常，现象是无预期的卡顿。。我也没办法，想使用国内 CDN 加速，域名必须备案。

![域名](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/image-20211203152728270.png)

当时配置那个 A 记录，CNAME 记录啥的根本不知道是什么东西，也不知道 DNS 是什么，就是配，成功了就行，不成功就猜，一个个试呗。现在想想，真的是走了不少弯路，如果能系统地学一下多好。不过这些问题也都在我后来的实践以及学习过程中逐一解决了，现在遇到问题也不用像没头苍蝇一样乱撞了，这种感觉很不错 :)

这件事也让我大致理解了一句老话，大致是这么说的：真正厉害的技术人员不是说他写程序一定要多么多么厉害，而是他有非常强悍的问题定位能力（trouble shooting），能解决别人解决不了的问题，而这一切都源自于无数经验的积累以及深度的思考。

下面说我的最后一次迁移：)

> 之所以有两个部分是因为买了域名后才发现必须要国内域名并且备案，才能加速国内。我买的是国外域名所以没办法，最后就用 GitHub Page + 自定义域名了。

## GitHub Page + 自定义域名

这种方案比较简单（因为GitHub 都帮我们做了），这也是我现在的方式，只不过我的域名是国外的，所以没办法使用 CDN 加速。

你首先需要创建一个名为 `<YourGitHubName>.github.io` 的仓库，比如 `sh1luo.github.io`，然后购买一个域名（国内国外都行，国内要备案），因为我们是要使用 GitHub 的自定义域名，所以需要使用 [CNAME](https://baike.baidu.com/item/CNAME/9845877?fr=aladdin) 记录，在域名服务器处添加两条CNAME 记录 ，就像这样

![DNS记录](https://gitee.com/sh1luo/imgs/raw/master/imgs/image-20210126230446099.png)

我是国外的域名，不能使用国内 CDN 加速，正好 CloudFlare 提供免费全球 CDN，虽然效果一般，但是它提供的免费功能也是非常的多，包括各种流量统计分析，也是很良心了。想使用 CloudFlare 当 DNS 服务器做法也非常简单。注册一个账号填上域名信息，然后会提供给我们两个 DNS 服务器域名，我们把原域名服务器商的 NameServers 改成新解析服务器提供的就好了。

![](https://gitee.com/sh1luo/imgs/raw/master/imgs/image-20210126231932450.png)

当然，如果你本来就是国内域名，就不用这么麻烦了，直接添加两条 CNAME 记录，然后在 GitHub Pages 仓库的发布分支放一个 CNAME 文件，文件内容就是你的 CNAME 地址就可以了，它会自动帮你设置为这个域名并搞定一切的:)

最终应该是这样：

![](https://gitee.com/sh1luo/imgs/raw/master/imgs/image-20210126232019604.png)

## CDN加速

如果你是国内的域名但是是国外的空间，就可以使用 CDN 加速了，加速区域选国内。这里需要注意源站地址由于是 GitHub Pages ，而 GitHub Pages 有 4 个 IP。都写上一行一个，回源 HOST 写你自己地址就可以了。这个回源 HOST 实际上就是 HTTP 头里的 host 字段，如果同一台机器上有多个服务的话，用来标识是哪一个服务，比较常见就是一个 IP 地址上配置了多个域名，就是通过这种给 host 首部字段的方式区分的不同 Web 站点。

配置完源站信息后，会生成一个 CDN 域名，比如我的是 `kcode.icu.cdn.dnsv1.com` ，然后再添加一条 CNAME 记录指向这个域名就搞定。这样配置过，你的网站经过缓存后国内访问速度能达到非常恐怖的速度，可以试着 ping 一下哦。

不过我这里是尝试了一下，发现国内都是不支持加速国外域名，所以放弃了。

![](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/image-20210118184423991.png)

## 自动化构建

自动化构建意思是说你只需要完成博客内容部分，其他生成静态页面，打包，发布部署等功能都交给一套脚本去完成。这里介绍我曾经体验过的几种。

### Github Actions

这是 Github 提供的功能较为全面的自动化部署解决方案，使用方法有两种，一是在 `.git` 文件的同级目录下创建一个 `.github/workflow` 目录，然后新建 `gh-pages.yaml` 文件，另一个是在 Web端登录进入你 `yourname.github.io` 仓库， `Code` 栏右侧的 `Action` ，点进去图形化创建并编辑文件即可，这里展示我的 Action 脚本：

```yaml
name: GitHub Pages

on:
  push:
    branches:
      - master
  pull_request:

jobs:
  deploy:
    runs-on: ubuntu-20.04
    concurrency:
      group: ${{ github.workflow }}-${{ github.ref }}
    steps:
      - uses: actions/checkout@v2
        with:
          submodules: true  # Fetch Hugo themes (true OR recursive)
          # fetch-depth: 0    # Fetch all history for .GitInfo and .Lastmod

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v2
        with:
          hugo-version: '0.80.0'
          extended: true

      - name: Build
        run: hugo --minify

      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        if: ${{ github.ref == 'refs/heads/master' }}
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          cname: kcode.icu
```

也比较好理解，就是执行 `hugo` 命令然后创建一个 CNAME 文件用于自动设置一个自定义域名，然后推到 `gh-pages` 分支。

这种方案的优点是自定义程度高，缺点相对就是需要自己全权控制写一个控制脚本，有一定学习成本。

这是我的自动化构建执行结果：

![image-20210331160251498](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/image-20210331160251498.png)

### Gitee Page

Gitee 提供了常见的几个博客框架的自动化部署功能，Hugo，Hexo 和 Jekyll。也就是说，只要你根目录下有对应框架的 `yaml` 配置文件，在你每次将最新内容推至仓库时就会自动执行自动化构建，并把最新页面推到前端页面上，比较省心。

优点是国内速度比 Github 快，毕竟服务器近，缺点是每次推完还要手动点更新，自动的一年 99RMB。

![image-20210331155953211](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/image-20210331155953211.png)

## 画图工具

这里主要介绍我使用的两个画图软件。

> 2021-06-19 16:44:13 更新

### Diagram

原来这个软件叫 draw.io，后来改名为 [Diagram](https://www.diagrams.net/)。

我之前一直使用这个工具画图，优点是免费，功能丰富，暂无发现缺点 :joy: 推荐给要求较高的同学使用，画彩色图，花里胡哨图。

![image-20210619170357266](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/image-20210619170357266.png)

### Ascii

Ascii 图是我看 [曹大博客](https://xargin.com/diagram-tools-intro/) 了解到的，可以说是一见面就夺走了我的所有抵抗力，我曾经还觉得在画编程方面的图这一块，Diagram 完全够用了，就好比 “任何比 C语言复杂的语言都能用 C语言实现” :sunglasses:

但是当我看到这种风格的图我再也不想用其他工具了，因为它完全够用了（装逼完美

毕竟曹大在讲 plan9 汇编时说过，学习的最大动力就是装逼，不服可以去线下面基他 :smile:，这种风格的图真的 geek 风拉满，“程序员味”十足。

![image-20210619170049500](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/image-20210619170049500.png)

说点正经的，我喜欢这种图最大的优点是 **简洁**，无他。我不用操心颜色搭配，字体大小，迁移存储等一切问题，只专心图所能表达出的含义就 OK 了。这里推荐两个站点：

- asciiflow（<https://asciiflow.com/>）
- Textik（<https://textik.com/>）

### Sketch

这个软件是比较专业的设计师使用的，也可以用来画一般的文章插图，缺点是收费，只能在 Mac 下使用。我没有使用过，可以自行搜索。

## 说在最后

这里说几点我个人看法。

- 博客要**注重内容**，我看好多人把界面弄的 **过于花哨** 不注重实际内容，我觉得如果你内容很丰富的情况下可以适当美化，但是弄个 BGM 或者动态换图什么的还是不要了。
- 多踩坑不一定是坏事，在大学这个试错成本很低的环境里就要多尝试，在踩坑的过程中把基础打牢，锻炼问题定位能力，多思考，多总结，日积月累肯定有所提升。
- 写博客给别人看的同时要多去看别人的成果，尤其是大佬们的，进步很快。
- 最后一点也是最重要的，不要主要依靠别人的博客学习，大部分博客不系统，甚至有的博主不理解就生搬硬套，很容易给新人带来误解。努力学习一手资料，官方文档、书籍都是不错的选择，其次才是较为系统阐述的博客、零散的博客。