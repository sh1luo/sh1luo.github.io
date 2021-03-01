---
title: "深入理解 Go string与slice"
date: 2021-02-15 23:35:20
tags:
  - Go
  - 源码
---

123

## 数据结构

我们先通过标准库源码来简单看一下。string 和 slice 的数据结构都定义在 `reflect/value.go` 中，分别对应着 [StringHeader](https://github.com/golang/go/blob/ac0ba6707c/src/reflect/value.go#L1983) 和 [SliceHeader](https://github.com/golang/go/blob/ac0ba6707c/src/reflect/value.go#L1994) 。

```go
type StringHeader struct {
	Data uintptr
	Len  int
}

type SliceHeader struct {
	Data uintptr
	Len  int
	Cap  int
}
```

定义非常简单，Data 表示底层数据的地址，Len 表示长度，Cap 表示容量。容量评估了当前切片最多能容纳多少字节元素，而长度表示当前已经存储多少个字节了，切片只是对底层数据的引用：

[图片]

字符串就是字符的数组，我们先来看个小程序的例子：

```go
package main

func main() {
	s := "abc"
	println(s)
}
```

我们执行 `go tool compile -S main.go` 使用自带工具包查看汇编代码，可以看到有这样一段信息：

```
...
go.string."abc" SRODATA dupok size=3
        0x0000 61 62 63    abc
...
```

很直观的可以看到字符串被分配到了 RODATA 区段，也就是只读区段（Read Only），也就是说 **Go 字符串是不可修改的**。





