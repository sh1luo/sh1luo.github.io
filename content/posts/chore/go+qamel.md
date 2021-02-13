---
title: "Go+QML构建桌面应用"
date: 2020-03-23 14:51:15
tags:
  - QML
  - Go
  - GUI
---

## 引文

开发的项目是直播助手，相关介绍在 [B站直播协议分析上](http://shiluo.design/2020/03/14/B%E7%AB%99%E7%9B%B4%E6%92%AD%E5%8A%A9%E6%89%8B%E5%BC%80%E5%8F%91%5B%E4%B8%8A%5D/) 有介绍，这里说一下技术选型方面遇到的问题，踩的坑，希望给后续的人一点建议和参考。

## 技术选型

因为当时第一步的主要想开发的功能是弹幕点歌，但是在稍做分析之后发现如何对 MP3 文件进行解码播放是个问题，自己实现可能略显复杂，也不是这个工具的主要想解决的问题。然后就考虑到使用什么组件来解码并播放音乐。

**最初**的想法是另写一套前端，和已经写好的这套后端进行通信，来呈现内容，播放音乐等，这是一定可以实现的，但是同一条信息进行两次传输效率太低，于是放弃，想在同一端执行，增加效率。Go 确实不擅长写 GUI 程序（C#完美。。），决定使用 [qamel](https://github.com/go-qamel/qamel)来使用开发，其和 [therecipe](https://github.com/therecipe/qt) 比较如下：

- 轻量（只使用少量的类）。构建简单的 QML 应用，比如 `QApplication`、 `QQuickView` and `QQMLApplicationEngine`。而 `therecipe/qt` 绑定了所有的 QT 模块。
- 安装简单。需要拿到编译好的 qamel 二进制文件（你可以选择自己编译构建，也可以选择直接从别人手里获取），放入 `path` 环境变量，再设置好配置，就可以构建自己的引用了。而 `therecipe/qt` 需要执行 `setup` 等一系列安装过程，繁琐且容易失败。
- 编译速度快。因为绑定部分代码是手动写的，使得绑定安装过程非常快，而 `therecipe/qt` 是安装时即时生成的，所以**非常慢**，可以自己体验一下。。

> 还有个缺点，目前跨平台编译只支持 windows 和 linux，macOS 作者未测试，目前未知。而`therecipe/qt` 支持 Linux, Windows, macOS, Android, Sailfish, Ubuntu Touch, WASM, and iOS各种平台。

## 坑在哪

> 以下均是在 Windows ，amd64 位环境下的结果。

- 不要在系统自带 CMD 或 PowerShell 中构建应用，不然会报代码第二行找不到 `QApplication` 的错误，换用 `cmder` 就可以解决，这个问题已经被证实，但是并未找到原因。

- 目前（Latest commit[72f913c](https://github.com/go-qamel/qamel/commit/72f913c4bdc9e8cf6f99d511c5eaa83233d36df5)on 27 Nov 2019），**不要用 Qt5.14.1及以上版本**，但是版本号要大于5.11，不然都会报错。比如图示：

![版本原因的错误](http://cdn.shiluo.design/aaa.png)

因为作者基本不维护，所以提的问题也没解决，目前也不确定是哪方面的问题，所以记录一下，希望以后使用此库的人能注意。

以上。
