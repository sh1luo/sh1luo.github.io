---
title: "手写一个RPCg（上）"
date: 2020-11-28 15:45:13
tags:
  - Go
  - RPC
  - 框架
---

# 须知

可能看到这里的一部分人还不知道什么是 RPC，也不知道为什么要用 RPC，内心：HTTP不香吗？那么你需要首先看一下这篇文章：

> [你觉得HTTP哪都好用是因为你不知道RPC]()

## 已经实现的

这篇文章我会带你手写一个简易版本的 RPC 框架，这个框架会支持如下这些功能：

- 多种网络传输方式
- 服务端自动注册可导出服务
- 可以心跳保活的注册中心
- 服务注册与服务发现
- 多种序列化方式
- 超时控制
- 一些负载均衡策略，一致性哈希、平滑带权轮询等

## 未来需要做的

- 自定义的代码生成插件

- 一种压缩方式

- 基于服务器时延的负载均衡策略？

## 心里有数

”切忌重复造轮子“这句话你应该听过，不过这个”框架“的目的是带领我们大致了解 RPC 框架的工作过程，目标并不是工业级应用，我想你也一定清楚用框架和自己写框架对框架的理解程度有什么区别。也不必把 RPC 想成多么”高端“的技术，RPC 也只是一个调用，微服务的一个组件，从小的地方出发更容易让人接受罢了。好了，话不多说，让我们正式开始。

# 俯瞰RPCg

![img](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/2C28140D4115AF68D708DAB4515B012C.jpg)

这个图向我们展示了最基本的 RPC 调用关系：服务端将自己的服务注册到注册中心，客户端从注册中心获取所有服务端的所有信息，在拿到这些信息之后带着自己的请求去访问某个服务端的服务。你可能会问为什么要多个”第三者“注册中心出来呢，我直接就只有客户端和服务端多方便，那你需要思考以下问题：

- 直接通信是不是需要将通信的地址等服务端信息硬编码到客户端的代码中？如果服务端节点数改变了怎么办，难道手动删改代码？
- 客户端怎么知道服务端可不可用？难道需要服务端开个服务专门去处理这类信息吗？这属于服务端的业务吗？
- ......

我想你应该大致能明白为什么需要这个注册中心了，就是屏蔽对方对己方的感知，通过一个第三方中介来提供/提出自己的服务/需求，这就够了，你可以类比 房产中介，婚介所等等机构，当然，注册中心还有很多功能，我们这里为了学习，就只提供这部分功能了，更多的需要留给你去探索 :)

我们再想想，我们现在有了三个主体，之前有不同的需求，怎么提供通信。业界有非常多的解决方法，比如 gRPC 的 HTTP/2.0，它的优势也是显而易见的：多路复用，pipelining 的通信方式，效率大幅提高，不必在等待对方的回复；首部压缩，这里我需要说明一下，RPC 调用大部分是服务端内部的互相调用，比如公司机房里 50 台机器之间相互调用，需要保证传输的效率，也就是说传送的数据要尽可能地小，这才有了 Protocol Buffers 的数据格式，所以经过压缩的首部数据量更小，效率更高。还有 tcp 连接，优势是简单等等。

等待更新....... 