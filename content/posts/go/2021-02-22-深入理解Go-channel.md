---
title: "深入理解 Go channel"
date: 2021-02-25 19:35:20
tags:
  - Go
  - 源码
---

Go 语言的 Channel 关键字是实现其原生并发编程的关键组成，你可能听说过 “不要通过共享内存的方式通信，要通过通信的方式共享内存”，这句话正是针对 Channel 说的。

Go 语言倡导通过通信的方式共享内存，也就是减少锁的使用，尽量都通过 Channel 来进行协程间通信。

其实这被称为一种并发模型名为 CSP（Communicating Sequential Processes），即通信顺序进程。

![csp](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/csp.svg)

两个实体 goroutine 通过 Channel  通信，收发消息。

## 数据结构

Channel 是一种 **带锁环状队列**，运行时结构定义在 [runtime/chan.hchan](https://github.com/golang/go/blob/41d8e61a6b9d8f9db912626eb2bbc535e929fefc/src/runtime/chan.go#L32) ，代码也比较容易理解。

```go
type hchan struct {
	qcount   uint           // 队列中元素数量
	dataqsiz uint           // 环形队列总大小
	buf      unsafe.Pointer // 底层数组指针
	elemsize uint16			// 元素大小
	closed   uint32			// 是否已关闭
	elemtype *_type 		// 元素类型
	sendx    uint   // 发送端下标
	recvx    uint   // 接收端下标
	recvq    waitq  // 接收端等待队列
	sendq    waitq  // 发送端等待队列

	// 保护 hchan 并发访问的字段
	lock mutex
}

type waitq struct {
	first *sudog	// 等待队列链表的头节点
	last  *sudog	// 尾节点
}
```

通过两个指针指向发送端和接收端接下来的操作位置，结合锁机制完成数据操作，这是很容易想到的并发处理方式。[runtime/chan.waiq](https://github.com/golang/go/blob/41d8e61a6b9d8f9db912626eb2bbc535e929fefc/src/runtime/chan.go#L53) 是阻塞等待 goroutine 的双向链表，每一个节点是一个封装了的 goroutine，被命名为 `sudog`，定义在 [runtime/runtime2.go](https://github.com/golang/go/blob/41d8e61a6b/src/runtime/runtime2.go#L345) 。

```go
type sudog struct {
	g *g

	next *sudog
	prev *sudog
	elem unsafe.Pointer // data element (may point to stack)
	...

}
```

`next` 和 `prev` 就是指向前后节点的指针，并且包裹了一个 goroutine 结构。

