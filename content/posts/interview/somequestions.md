---
title: "一些常见 Go 语言及面试问题的整理"
date: 2021-01-15 21:10:55
toc: true
tags:
  - 杂谈
  - Go
  - 面试
---

这篇博客记录一些关于面试常见的 Go 语言方面的问题，希望能帮到大家。

> 待完成

## Go make和new的区别，使用和底层？

两者都可以声明变量，例如 map，channelchannel，slice，以及结构体等等，我们常用make来初始化map，channel，而常用new 来初始化普通类型变量和结构体。

区别是make会分配底层所需的空间，而new只会分配该结构头部的空间。如果首部中并没有引用其他内存地址，那么new 和make是一样。

举个例子，当我们声明 map 时，实际上说获得了一个 hmap 类型的指针，指向 hmap结构体：

```go


```

如果我们使用make（map[type]type, 10），就会为map底层所使用的空间分配足够使用的bucket，如果使用new，则只分配hmap结构体所需内存，并不会分配底层所使用的空间，使用map也就无从谈起了。常见的一个错误示范就是通过 `var m map[int]int` 声明，然后直接 `m[1]=1` 来使用，这样就会直接因为空指针引用而panic！

## Go内存管理



## goroutine 什么时候会阻塞？



## goroutine有几种状态？

m操作g的时候有自旋与非自旋状态？



## 线程有哪些状态



## 注册中心挂了怎么办？

N节点，raft一致性？



## 反射底层原理？



## 通过反射执行函数，拿结构体tag？



## 锁机制？饥饿模式正常模式？锁底层原理？



## channel使用，坑，底层原理？