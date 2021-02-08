---
title: "深入理解 Go map"
date: 2021-01-22 23:35:20
tags:
  - Go
  - 源码
---

## 哈希表

几乎所有语言都有 [哈希表](https://en.wikipedia.org/wiki/Hash_table) 这个数据结构，能够在平均 O(1)，最差 O(n) 的时间复杂度增删改查元素，Go 语言哈希表的精妙设计使得它几乎不会出现 O(n) 的糟糕情况。这篇文章我就带你从使用到底层由浅入深地探究 Go map 的奥秘，一起作一个不只是会用的”大神“。

问题来源于实际，我们先看看这些问题 ：

- **声明**。当我使用 `:=`，`var`，`make`，甚至 `new` 声明 map 的时候，编译器帮我们做了什么事情，它们有什么区别？
- **增删改查**。使用 数组+链表 的情况下如何设计才能避免 O(n) 的最差情况？
- **注意事项**。map 的键有什么要求？map 是值类型还是引用类型，函数传参时会有上层影响吗？是并发安全的吗？

还有一个常识是 Go map 的**遍历是随机的**，即多次遍历输出的结果集不同。

### 设计方式/数据结构

Go map 实现哈希表使用的是 **数组+链表** 的形式，也就是使用链地址法解决的哈希冲突。这种方式桶的大小和元素个数之间没有关系，另外还有开放定址法，这是个宽泛的名字，具体包含线性探测法，再哈希法，平方探测法等等。

为了降低 map 操作的时间复杂度，引入了一个 [负载因子](https://github.com/golang/go/blob/41d8e61a6b9d8f9db912626eb2bbc535e929fefc/src/runtime/map.go#L70) 的概念，这个概念在其他实现哈希表这个数据结构的语言里也都有，比如 python 中这个值被定义为 2/3，Java 中是 0.75，这个值评估了哈希表里 **实际上最好只存** 多少比例的元素，而不是一直等到满载再处理，因为多到一定程度效率 **可能** 就低了。在 Go 语言里这个值被定义为 6.5，即每个桶里最多存 6.5 个，包括溢出桶。

当我们在 Go 语言中声明一个 map 的时候，实际上就是创建了一个 [hmap](https://github.com/golang/go/blob/41d8e61a6b9d8f9db912626eb2bbc535e929fefc/src/runtime/map.go#L115) 的结构体，它定义在 `runtime/map.go` 文件下，这个结构体包含了许多信息：map 的大小，桶数量、地址，溢出桶数量、地址等等。 哈希表就是实现一个映射关系，给出自变量 x，能够通过平均 O(1) 的时间复杂度方法找到这个元素所对应的因变量 y=f(x) 来对它进行操作。

```go
type hmap struct {
    count     int 		// map的大小，len()的结果就是这个字段值
	flags     uint8		// map的状态，有四个
	B         uint8  	// 桶数量的log_2对数，如B=5，桶数量就是2^5=32
	noverflow uint16 	// approximate number of overflow buckets; see incrnoverflow for details
	hash0     uint32 	// 哈希种子

	buckets    unsafe.Pointer // 桶数组的底层地址
	oldbuckets unsafe.Pointer // 旧桶数组的底层地址
	nevacuate  uintptr        // progress counter for evacuation (buckets less than this have been evacuated)

	extra *mapextra // optional fields
}

// mapextra holds fields that are not present on all maps.
type mapextra struct {
	// If both key and elem do not contain pointers and are inline, then we mark bucket
	// type as containing no pointers. This avoids scanning such maps.
	// However, bmap.overflow is a pointer. In order to keep overflow buckets
	// alive, we store pointers to all overflow buckets in hmap.extra.overflow and hmap.extra.oldoverflow.
	// overflow and oldoverflow are only used if key and elem do not contain pointers.
	// overflow contains overflow buckets for hmap.buckets.
	// oldoverflow contains overflow buckets for hmap.oldbuckets.
	// The indirection allows to store a pointer to the slice in hiter.
	overflow    *[]*bmap
	oldoverflow *[]*bmap

	// nextOverflow holds a pointer to a free overflow bucket.
	nextOverflow *bmap
}
```

真正存储数据的地方被称为桶，map 可以有许多桶，但是每个桶只能存储 8 个键值对，多出来的就要找到一个溢出桶放进去，每个桶的数据结构都是一样的，tophash 是键值经过哈希函数后的值高八位。

这里需要注意一点是，key 和 value 并没有按照 key1/key2/keyN，value1/value2/valueN 的方式存储，而是如图形式，是为了因为字节对齐造成的内存浪费，这一点在官方源代码里有说明。

![](https://gitee.com/sh1luo/imgs/raw/master/imgs/map_zipper.svg)



### 初始化



### 读写操作

#### 访问

#### 写入

#### 删除

#### 扩容

### 总结