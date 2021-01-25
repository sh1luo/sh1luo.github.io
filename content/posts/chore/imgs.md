---
title: "博客图床解决方案"
date: 2021-01-20 15:45:13
toc: true
tags:
  - 杂谈
  - 博客
---

很多人应该都听说过来人说过要写博客进行总结记录，一是说自己学习过程的复盘，二是在某些时候向不认识自己的人间接显示自己的大致水平。不过如果没有人“手把手”教的话我相信还会遇到各种各样的问题的，这篇文章就介绍一下在博客中必不可少的图片网络地址解决方法，也就是图床。它的目标是**在你写文章的过程中可以一键插入目标图片并自动上传到网络，就像你使用本地图片一样快捷。**

图床的目的就是把你的本地图片上传上去，从而能获得它的网络地址。当然了，只使用图床也是可以的，但是需要配合对应的工具上传拿 URL（比如 OSS）或者纯手动（GitHub/Gitee），~~非常不方便~~ 一点也不极客，所以需要配合其他工具一键快速拿到它对应的网络地址（URL），所以我在下面介绍了我使用到的工具，仅供参考。

> 评估用的稳定性指你上传的图片会不会在某个不确定的时间突然挂掉，让你的文章出现大量图片 404 丢失的情况。

# 图床

这里我介绍三种图床，列出优缺点。可以根据需要进行选择。

## GitHub/Gitee

![Gitee](https://gitee.com/sh1luo/imgs/raw/master/imgs/123.png)

[GitHub](https://github.com/) 和 [Gitee](https://gitee.com/) 是干什么的我就不多说了，它们也是可以作为图床使用的，前者境内访问较慢，后者较快。没有账号可以免费注册一个，然后随便创建一个公开仓库，把图片上传上去就可以获取它的 URL 了，比较简单粗暴。

优点：稳定性较好，空间无限，上手难度较简单

缺点：无法阻止盗链，无法管理（原本目的就不是作为图床，没有统计流量等功能）。

总结，如果你是新手，不担心自己的图片被别人**轻易获取** ，随缘使用图床，这个是首选。

## OSS

![aliyun OSS](https://gitee.com/sh1luo/imgs/raw/master/imgs/image-20210120131946016.png)

OSS （Object Storage Service）即对象存储服务，用来做个人博客的图床有点小题大做，腾讯云、阿里云等等提供 OSS 的平台都可以，一般需要续费，一年 50G 左右话 10 块钱左右。

优点：可控性比较强，提供了专业的平台，你能想到的各种需求基本都有，包括防盗链，流量统计与分析等。

缺点：对新手不友好，根据流量付费。

总结，如果你未来博客流量会不断增大，出于可控考虑选这个，流量较小的新人不考虑。

## 不稳定第三方

![SM.MS](https://gitee.com/sh1luo/imgs/raw/master/imgs/image-20210120132728890.png)

也可以使用这种第三方的图床，没有任何操作步骤，上传完就拿到 URL，当然事物都有两面性，这种极致快捷带来的就是不稳定，就跟当年的新浪图床一样，你不知道什么时候它就没了。。

优点：简单快捷打开一键就用，免费

缺点：不知道什么时候你的图片就被人家清了。。然后你的文章里的图片就全部 404 了。。

总结，随缘党首选不解释，懂得都懂。

# 工具

这里就介绍我使用的两个配合工具，其他的可以自行搜索。

## typora

[typora](https://typora.io/) 是一款 Markdown 文本编辑软件，我相信写过 Markdown 的都听说过，它的特点是真正的实时显示，不左右分栏，扩展性强，灵活可配置。我个人平时写 Markdown 文本都是使用这个软件，具体可以去它的官网首页看，十分推荐。

![实时转换](https://gitee.com/sh1luo/imgs/raw/master/imgs/GIF%202021-1-20%2018-44-01.gif)

## PicGo

![](https://gitee.com/sh1luo/imgs/raw/master/imgs/image-20210120134735352.png)

[PicGo](https://github.com/Molunerfinn/PicGo) 是一款使用 Node + Electron 开发的跨平台可视化图片上传开源软件，支持 N 种图床平台，配置灵活简单，最重要的是它支持插件功能，理论上支持任意图床平台的使用（需要提供相应上传下载的 API），可以自行开发插件。操作也比较简单，把图片拖到框里就可以拿到 URL。这张图是 gitee 相关配置，其他平台类似，只需若干个必要参数即可：

![配置](https://gitee.com/sh1luo/imgs/raw/master/imgs/image-20210120135009612.png)

## 配合使用

![PicGo配置](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/test.png)

前面说的这两种工具可以结合使用快速进行写作，在 typora 主界面上方，文件->偏好设置->图像，修改 PicGo 路径为你安装的路径下的 exe 地址。这样就可以做到你在 typora 里编辑时直接粘贴图片到文档里一键点击上传，非常方便。当然了，如果你不需要 typora，或者使用的是别的 Markdown 编辑器，也可以只使用 PicGo。

而且它是开源的，如果你有任何建议可以提 Issue 或者自己为它增加特性 :)

我这里就有一个相关需求，自定义重命名上传文件，我想将所有图片按照我自己的规则自动重命名后再上传，比如统一按照格式 `year-month-day-imgID` 这种格式，方便后续整理图片。当然了，这里只是抛砖引玉，更多的留给大家去探索 :)

最后配一个最终的成品 GIF 图给大家看一下效果：

![dddd](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/dddd.gif)

如果你有什么问题欢迎来找我玩，一起交流。
