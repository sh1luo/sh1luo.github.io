---
title: "谈谈最常见的 HTTP"
date: 2021-01-15 23:10:22
tags:
  - HTTP
---

标题的”最常见“我想应该没有什么争议，对大多数人来说日常生活中接触到最多的应用层协议就是 HTTP了，从聊天软件、浏览器页面再到各种游戏实现，它们无处不在。这篇文章我就带你来看一看这个处于 OSI 标准最上层、最常用也是最普通的 HTTP 它究竟有什么“东西”，一起作为一个不只是听说过的“大神”。

这篇博客我想阐述除书本概念之外的一些可能你 **理解不深刻** 的问题的 **个人理解**，希望对你有所帮助。

## HTTP是什么

超文本传输协议（Hypertext Transfer Protocol，HTTP），是一个应用层面上的，也就是软件双方通信的数据规则，是通信的基石。不然你发给我一串 @#$%$%^$%^，只有你能看懂，我怎么知道你说的是什么玩意？双方按照这个规则去通信，有什么需求都在这个规范里写好了发给对方，对方就知道你想干什么，就可以也按照这个规范给你回过去，就是这么简单。只是因为随着技术的发展，所遇到的问题越来越多，从功能需求，再到安全、效率、可读性等等，不得不提出一系列的解决方案去完善，最终变得很 ”臃肿“ 罢了。但是你应该明白，这就是一个为应用程序通信所提出来的一个基础通信协议。

## HTTP方法有什么“实际区别”

你可能听说过类似 “GET 和 POST 有什么区别” 这种问题，其实说到底从底层上来说，它们之间 **没有任何区别，仅仅是约定、规范。** 也就是说 **按照约定**，GET 方法的请求 **不应该** 携带请求体，并且在以前 [Postman](https://www.postman.com/) 这类客户端模拟软件也是不允许构造这类请求的，但是后来也是支持了。

但是，如果你强行带了请求体，是没有任何问题的。你甚至可以把 GET 方法携带上请求体用来登录，使用 POST 请求用来获取 HTML 等静态资源，用 DELETE 方法来为数据库增加一条记录，只要你后端程序员老哥不把你捶死（手动狗头） 🤣🤣🤣

## 各个版本之间的发展史

HTTP 比较重要的几个发展时间节点是 0.9、1.0、1.1、2.0 和 3.0，每一次的版本变迁都是为了解决前一个版本的性能不足或者功能不完善，我不推荐死记硬背，即使它被称为计算机八股文。

### http 0.9和1.1

在 HTTP 0.9 的时候只有 GET 方法，1.0 补充了 POST，DEL 方法完善语义，还添加了几个首部，这个阶段的 HTTP 主要就是完善功能。

1.0 和 1.1 的最大区别就是长短连接了。在 HTTP 1.1 将长连接设置为了默认，也就是：

```
Connection: keep-alive
```

在这之前这个字段的默认是 `close`，长连接的好处是显而易见的，由于 HTTP 是基于 tcp，如果总共传输三个文件，1.0 的时候需要建立和断开三次连接，1.1 的时候就只需要一次了。但是现在的问题还很明显，客户端想拿这三个文件，还是要三次请求，显然不合理。而且如果你打开开发者工具查看过 HTTP 的报文不难发现，即使你就需要几十个字节的 json 返回数据，服务端也要给你回那么长的 HTTP 报文，冗余信息的大小都超过了你的需要信息大小，这显然也不河里。所以这些问题就在 HTTP 2.0 版本里解决了。

### http 2

HTTP 2.0 主要有这些特色：

- 协议协商机制，可以选择使用 HTTP/1.1 还是 HTTP/2 或者其他。
- 高度向下兼容，原来 HTTP/1.1 的方法，状态码，URI和首部都不用改变。
- 首部压缩，通过双方都保存一份静态和动态表，通过发送双方都知道的 Index 来表明使用的是哪个首部字段。
- 服务端推送，解决只能客户端请求，无法服务端主动返回的问题。
- 二进制分帧，请求的流水线形式等等。

#### 多路复用

如果你想请求 100 个文件，在之前你可能想要建立 100 个 TCP 连接同时请求，但是实际上浏览器会限制数量为 2~6 个，总之还是需要至少 2 个 TCP 连接。但是 HTTP/2 可以复用一个连接，这就减少了建立连接所需的时间。

![multiplexing](https://gitee.com/sh1luo/imgs/raw/master/imgs/multiplexing.png)

#### 首部压缩

### 在线体验

#### demo1

看到这里，你应该对 HTTP 2 的优势有了一个理性的认知了，你可以点一下这个 [在线链接](https://http2.akamai.com/demo) 来**直观地感受**它们的速度差异。

#### demo2

## 小结
