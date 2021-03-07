---
title: "深入理解 Go channel"
date: 2021-02-25 19:35:20
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

还有一个常识是 Go map 的 **遍历是随机的**，即多次遍历输出的结果集不同，这个的原因会在后面提到。

### 设计方式/数据结构

Go map 实现哈希表使用的是 **数组+链表** 的形式，也就是使用链地址法解决的哈希冲突。这种方式桶的大小和元素个数之间没有关系，另外还有开放定址法，这是个宽泛的名字，具体包含线性探测法，再哈希法，平方探测法等等。

为了降低 map 操作的时间复杂度，引入了一个 [负载因子](https://github.com/golang/go/blob/41d8e61a6b9d8f9db912626eb2bbc535e929fefc/src/runtime/map.go#L70) 的概念，这个概念在其他实现哈希表这个数据结构的语言里也都有，比如 python 中这个值被定义为 2/3，Java 中是 0.75，这个值评估了哈希表里 **实际上最好只存** 多少比例的元素，而不是一直等到满载再处理，因为多到一定程度效率 **可能** 就低了。在 Go 语言里这个值被定义为 6.5，即每个桶里最多存 6.5 个，包括溢出桶。

当我们在 Go 语言中声明一个 map 的时候，实际上就是创建了一个 [hmap](https://github.com/golang/go/blob/41d8e61a6b9d8f9db912626eb2bbc535e929fefc/src/runtime/map.go#L115) 的结构体，它定义在 `runtime/map.go` 文件下，这个结构体包含了许多信息：map 的大小，桶数量、地址，溢出桶数量、地址等等。 哈希表就是实现一个映射关系，给出自变量 x，能够通过 **平均** O(1) 的时间复杂度方法找到这个元素所对应的因变量 y=f(x) 来对它进行操作。

```go
type hmap struct {
    count     int 		// map的大小，len()的结果就是这个字段值
	flags     uint8		// map的状态，有四个
	B         uint8  	// 桶数量的log_2对数，如B=5，桶数量就是2^5=32
	noverflow uint16 	// 溢出桶的数量
	hash0     uint32 	// 哈希种子

	buckets    unsafe.Pointer // 桶数组的底层地址
	oldbuckets unsafe.Pointer // 旧桶数组的底层地址
	nevacuate  uintptr        // 迁移进度

	extra *mapextra // 溢出桶
}

type mapextra struct {
	overflow    *[]*bmap
	oldoverflow *[]*bmap

	// 指向下一个空闲溢出桶
	nextOverflow *bmap
}
```

需要注意的是，如果 map 的键值都不包含指针并且是内联的，那么我们就会标注 map 为 ”不含指针类型“，这样就可以避免 GC 扫描 map，从而避免在 map 在过大时由于指针过多造成的 GC 扫描对象过多而缓慢的问题。所以将所有关于溢出桶的指针都放在了 extra 字段中。mapextra 字段保存了与溢出桶相关的信息，`overflow` 指向当前桶 `hmap.buckets` 的溢出桶，`oldoverflow` 指向旧桶 `hmap.oldbuckets` 的溢出桶。

真正存储数据的地方是 [bmap](https://github.com/golang/go/blob/ac0ba6707c1655ea4316b41d06571a0303cc60eb/src/runtime/map.go#L149)，map 有 2^B 个 bmap，但是每个 bmap 只能存储 8 个键值对，多出来的就要找到一个溢出桶放进去，每个桶的数据结构都是一样的，bmap 结构只有 tophash 字段是因为 map 的 key 和 value 是需要 **在编译时计算确定**，所以需要在编译时动态构造桶结构。唯一的 tophash 字段是键值经过哈希函数计算后的值高八位。

```go
type bmap struct {
	tophash [bucketCnt]uint8
}
```

此外，动态运行时构造的 key 和 value 键值对并没有按照 key1/value1、key2/value2、...、keyN/valueN 的方式存储，而是如图形式，是为了避免因为字节对齐造成的内存浪费，也是因为 CPU 从内存中读取数据是每次读取固定大小的块（因为数据总线条数固定），这块内存也并不是连续的，这里不展开说了，总之，如果采用 key1/value1、key2/value2、...、keyN/valueN 的方式，如果 map 是 map[int64]int8 的时候，每个键值对就会由于内存不对齐造成 7 字节的内存浪费，其实也并不一定浪费，现在很多 CPU 也可以读取多块内存然后拼接组合成最终的数据，但是这样性能并不好。这一点在官方源代码里的 [bmap](https://github.com/golang/go/blob/41d8e61a6b9d8f9db912626eb2bbc535e929fefc/src/runtime/map.go#L148) 结构体注释中有说明。

![](https://gitee.com/sh1luo/imgs/raw/master/imgs/map_zipper.svg)



### 初始化

Go 语言初始化 map 的方式有两种，字面量和运行时。

#### 字面量 ":="

```go
m := map[int]string {
    1: "go",
    2: "lang",
}
```

几乎所有语言都会提供字面量的方式进行初始化，Go 语言里的字面量初始化是使用了 ":=" 符号，这样来代表创建一个局部变量。Go 语言里的 map 也可以通过这种方式初始化，但是需要注意的是，还有一种初始化方式 `var m map[Type]Type` ，如果仅仅这样声明后就直接使用 `m[key] = value` 来写入是会 panic 的，因为没有分配实际内存。

通过这种方式初始化的 map 会调用 [maplit](https://github.com/golang/go/blob/ac0ba6707c1655ea4316b41d06571a0303cc60eb/src/cmd/compile/internal/gc/sinit.go#L753) 函数来执行具体的创建逻辑：

```go
func maplit(n *Node, m *Node, init *Nodes) {
	a := nod(OMAKE, nil, nil)
	a.Esc = n.Esc
	a.List.Set2(typenod(n.Type), nodintconst(int64(n.List.Len())))
	litas(m, a, init)

	entries := n.List.Slice()

    // ...

	if len(entries) > 25 {
		// 如果数量非常多（指大于25个），就放进数组中循环处理。

		// 构建 [count]Tindex 和 [count]Tvalue
		tk := types.NewArray(n.Type.Key(), int64(len(entries)))
		te := types.NewArray(n.Type.Elem(), int64(len(entries)))
        
        // 后续循环插入，类似
        // for i = 0; i < len(vstatk); i++ {
		//	 map[vstatk[i]] = vstate[i]
		// }
        
        ...
    }
```

不管是哪种情况，最终都会通过 make 来创建哈希表数据结构并且通过 map[key] = value 的形式插入数据。

#### 运行时 "make"

使用 make 创建 map 时有两种情况，一种是不给出大小，或者大小小于 8 的时候，会调用 [makemap_small](https://github.com/golang/go/blob/ac0ba6707c1655ea4316b41d06571a0303cc60eb/src/runtime/map.go#L292) 来快速初始化一个 map：

```go
func makemap_small() *hmap {
	h := new(hmap)
	h.hash0 = fastrand()
	return h
}
```

显而易见，这种的方式的 map 是声明在堆上的。除了这种方式之外，map 会通过 [makemap64](https://github.com/golang/go/blob/ac0ba6707c1655ea4316b41d06571a0303cc60eb/src/runtime/map.go#L282) 来将 map 的大小设置为 int32 后再调用 makemap 函数进行创建的主要逻辑：

```go
func makemap(t *maptype, hint int, h *hmap) *hmap {
	mem, overflow := math.MulUintptr(uintptr(hint), t.bucket.size)
	if overflow || mem > maxAlloc {
		hint = 0
	}

	if h == nil {
		h = new(hmap)
	}
	h.hash0 = fastrand()

	B := uint8(0)
	for overLoadFactor(hint, B) {
		B++
	}
	h.B = B

	if h.B != 0 {
		var nextOverflow *bmap
		h.buckets, nextOverflow = makeBucketArray(t, h.B, nil)
		if nextOverflow != nil {
			h.extra = new(mapextra)
			h.extra.nextOverflow = nextOverflow
		}
	}

	return h
}
```

[makemap](https://github.com/golang/go/blob/ac0ba6707c1655ea4316b41d06571a0303cc60eb/src/runtime/map.go#L303) 函数做了这几件事：

- 用桶的个数*8，判断内存是否足够分配，会不会溢出，如果会的话就置 0。

- 声明一个 map 结构体变量，初始化一个随机数用于哈希函数的计算。

- 用 make 内置函数的第二个参数 hint 判断出需要多少个桶，转换为对数存到 B 中。

- 如果 B 是 0 的话，就不分配内存，后续用的时候懒加载分配，所以从这里我们也能明白为什么平时说提前给出 map 的大小后续使用速度更快了。如果不是 0，就调用 [makeBucketArray](https://github.com/golang/go/blob/ac0ba6707c1655ea4316b41d06571a0303cc60eb/src/runtime/map.go#L344) 分配底层的桶内存和溢出桶内存。

这里会有一个判断 `nextOverflow != nil` ，这里就涉及在什么情况下初始化时要提前分配溢出桶，Go 语言是这样解决的：如果 B 大于 4，那么就认为后续使用溢出桶的概率比较大，就会预先分配 `2^(B-4)` 个溢出桶。然后分配专门用来描述溢出桶的结构 `hmap.extra`，其中指向下一个溢出桶地址的  `nextOverflow ` 字段就指向分配好的溢出桶首地址。

正常桶和溢出桶的地址是连续的，只是被不同的字段引用而已，如果溢出桶不够用，会调用 [runtime/newobject](runtime/newobject) 分配新的溢出桶。直到达到元素数量过多需要全量扩容或者重新哈希等量扩容，这个问题下文会详说。

### 读写操作

Go 内置数据类型 map 是并发不安全的，也就是说多个 goroutine 同时对 map 执行写入操作会导致程序发生 panic 中断。官方解释说这是因为大多数情况下 map 并不需要并发安全，如果为所有 map 都加上并发操作的特性会使得大多数场景性能下降，为此 Go 在 1.9 版本引入了一种并发安全的 map 类型 [sync/map](https://github.com/golang/go/blob/41d8e61a6b/src/sync/map.go#L27) ，留给读者自行探索。

#### 访问

map 的访问有两种形式：

```go
value := m["I'm a Key"]
```

Or

```go
value, ok := m["I'm a Key"]
```

第二种方式的第二个返回值是个布尔类型，代表该键在 map 中是否存在，类似于数据库或者其他概念中的 NULL 值，目的是为了不和所有该类型值冲突。两种方式的底层调用分别对应着 [runtime/mapaccess1](https://github.com/golang/go/blob/ac0ba6707c/src/runtime/map.go#L389) 和 [runtime/mapaccess2](https://github.com/golang/go/blob/ac0ba6707c/src/runtime/map.go#L452) ，Go 语言会在运行时决定使用哪种方式。

```go
func mapaccess1(t *maptype, h *hmap, key unsafe.Pointer) unsafe.Pointer {
    // ...
	hash := t.hasher(key, uintptr(h.hash0))
	m := bucketMask(h.B)
	b := (*bmap)(add(h.buckets, (hash&m)*uintptr(t.bucketsize)))
    // ...
	top := tophash(hash)
bucketloop:
	for ; b != nil; b = b.overflow(t) {
		for i := uintptr(0); i < bucketCnt; i++ {
			if b.tophash[i] != top {
				if b.tophash[i] == emptyRest {
					break bucketloop
				}
				continue
			}
			k := add(unsafe.Pointer(b), dataOffset+i*uintptr(t.keysize))
			if t.indirectkey() {
				k = *((*unsafe.Pointer)(k))
			}
			if t.key.equal(key, k) {
				e := add(unsafe.Pointer(b), dataOffset+bucketCnt*uintptr(t.keysize)+i*uintptr(t.elemsize))
				if t.indirectelem() {
					e = *((*unsafe.Pointer)(e))
				}
				return e
			}
		}
	}
	return unsafe.Pointer(&zeroVal[0])
}
```

mapaccess1 的返回值是一个指向目标值的指针，如果不存在的话会返回该类型的零值而不会返回 nil。

依次做了这些事：

- 通过 map 最开始初始化的哈希种子，用哈希函数计算出该键的哈希值 `hash`，这里的哈希函数使用了依赖注入的方式，并不固定。
- 计算桶的位掩码 `m`，也就是 B-1，用于后续做与运算确定该键位于哪个桶中。
- 与运算找到桶，桶的首地址+桶序号*桶大小动态计算出目标桶地址 `b`，取高八位哈希值 `tophash`，这里是通过位运算的方式取高位的，因为除法代价太高。
- 最后从桶的第一个 cell 开始，到最后一个溢出桶的最后一个 cell 为止遍历，先比较 tophash，如果一致了就用 tophash 值的下标和 map key 的大小计算出该 key 的偏移，再比较一次，这样可以加速查找，

第二种形式的底层调用是 [mapaccess2](https://github.com/golang/go/blob/ac0ba6707c1655ea4316b41d06571a0303cc60eb/src/runtime/map.go#L452) ，过程和第一种类似，只是在最后的两个 return 处多返回了一个布尔值：

```go
				// ...
				return e, true
			}
		}
	}
	return unsafe.Pointer(&zeroVal[0]), false
```

还有一个函数 [mapaccessK](https://github.com/golang/go/blob/ac0ba6707c1655ea4316b41d06571a0303cc60eb/src/runtime/map.go#L511) ，返回的是 map 的 key 和 value，用于 map 的 range 函数遍历，过程类似，不赘述了。

#### 写入



#### 删除

#### 扩容

### 总结

Go 语言的 map 使用了数组+链表实现的哈希表，引入了溢出桶的概念来减少桶的扩容，实现了平均 O(1) 的时间复杂度内访问元素，基本不会出现最坏的情况。经过哈希计算后，用低 B 位确定桶位置，高 8 位比对找到 tophash，再通过偏移找到 key/value，或者执行插入或者新增溢出桶等等逻辑。

不管你使用字面量的方式还是 make 的方式声明 map，都是对应底层的 hmap 结构，获得了一个指向 hmap 的指针，并且 Go 语言针对不给出初始大小的 map 还进行了快速初始化的优化，针对 map 的大小过大（hmap.B 大于4），提前建立溢出桶的优化。

Go 提供了两种方式访问 map 中的元素，可以获得两个返回值，第二个返回值可以忽略，这用于空键值对的判断，类似于数据库中的 NULL，不和任何值冲突。并且 map 的遍历访问是随机的，这是因为每次遍历时会通过 fastrand 生成一个随机数，随机选择一个桶，再随机选择桶中的一个元素，先遍历完该桶，再顺次遍历后续的桶。map 是可以并发访问的，因为这并不会有任何冲突发生。