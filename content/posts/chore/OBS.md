---
title: "OBS/Bilibili 直播姬的显示器捕获黑屏解决方案"
date: 2020-04-26 11:34:13
tags:
  - 踩坑
---

> OBS 与 Bilibili直播姬 操作类似。

## 问题起因

由于我最近重新安装了系统，在重新下载 OBS 后发现捕获不到桌面。我之前解决方法就是直接在**显卡控制面板** 里将 OBS 设置为集显就行了。但是这次设置了也不行，有可能是我下载的显卡驱动版本不对。。于是就找到了这个终极解决方案。

![N卡设置](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/image-20211203163901757.png)

## 问题环境

操作系统：Win10 64位 专业版 - 1909

CPU 集成显卡型号：Inter(R) UHD Graphics 630

独立显卡型号：NVIDIA GeForce GTX 1050

OBS 版本：25.0.4(64 bit)

> 注：配置和我不一样也有可能解决，不用纠结

## 问题描述

![](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/obs-noscreen.png)

在来源中添加**显示器捕获后** ，是黑屏，**无法捕获到显示器**。

## 问题分析

目前网上能搜集到的解决方案大部分是以下几种：

- 右键 OBS 属性 - 兼容性 - 兼容模式 - 以兼容模式运行这个程序（win7）设置 -  以管理员方式运行
- 桌面上右键打开 NVIDIA 控制面板，管理 3D 设置 - 程序设置，找到 OBS，设置为集成图形。

![任务管理器最下面](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/obs-gpu.png)

但是我都试了都解决不了，我就去搜了一下问题的原因，**最终**发现 OBS **只能捕捉到和自己跟自己使用相同显卡的应用**，然后我右键打开任务管理器，发现笔记本桌面使用的是我的集显。所以就需要把 OBS 设置为应用集显。

## 解决方法

<img src="https://blogimagee.oss-cn-beijing.aliyuncs.com/images/obs-setting.png" alt="图形设置" style="zoom:50%;" />

左下角开始按钮 - 设置 - 系统 - 显示 - 图形设置 - 经典应用里浏览添加 OBS ，点击选项，设置为节能，节能就是使用集显。然后你再打开 OBS......

这时候你就会发现你成功了。

其他的推流软件也一样，比如什么 B 站直播姬等同理。

以上。