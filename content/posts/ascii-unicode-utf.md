---
title: "一文搞懂 ASCII、Unicode与UTF 编码"
date: 2020-09-18 09:27:13
toc: true
tags:
  - 字符集
---

## 起因

最初在学习 Go 语言的各种类型时发现内置字符类型有两种类型，一种是 Byte（1 字节表示一个 ASCII 字符），还有一个就是 rune 类型，可能从其他语言转过来的开发者都会对 rune 觉得非常陌生，我自己也是仅仅停留在 **会用** 的阶段上，久而久之就会特别乱，所以写一篇博客介绍一下各种字符以及编码方便彼此学习，彻底解决这类问题。

## 什么是ASCII，为什么又要引入Unicode

![image](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/ascii.png)

都应该了解过 ASCII、Unicode、Unicode 码点、UTF-8等一系列名词。先说 ASCII（American Standard Code for Information Interchange: 美国信息交换标准代码），它是一种**字符集**，说白了就是一个字符和数字的**一一对应关系**，你想找这个字符怎么办，计算机又不认识字符？给出他的对应的数字就行了。最初只有美国等一些使用英文的国家使用，所以 128 个字符完全够用，它包含了标点符号、数字和字母等。但是随着世界上使用计算机的国家越来越多，这 128 个字符是完全不够用的。所以 **Unicode 字符集** 就出现了。Unicode 包含了世界上绝大多数的字符，给他们提供了一一对应关系，比如“知”字对应 30693，即 U+77e5（16 进制形式）。所以说白了 ASCII 和 Unicode 就是**一种字符集**，**一种字符对应关系**，Unicode 中每个字符被称为一个 **Code Point**（码点），而 Go 语言中的 rune 类型正是代表了这样一个单位，即一个 rune 代表了一个 unicode 字符。

那么大家肯定都听说过 UTF-8，UTF-16 吧，那问题来了， UTF 又是什么呢，UTF-8 和 UTF-16 到底又有什么关系呢？

## UTF（Unicode Transformation Format）

从字面上你就应该能看出来，这就是一个 Unicode 转换格式。什么是转换格式，为什么需要转换格式？上文说了 Unicode 就是提供了字符间的一一对应关系，比如“知”对应了 30693，那计算机怎么表示这个数（计算机只认识二进制）？很显然，它首先必须要做到 **准确识别每一个字符**。

比如有这么一串二进制串：`1101 0101 1010`，如果表示每个字符所需的二进制位数相同，那么这个问题很容易解决，一一对应呗。但是如果长度不同怎么办？

那就需要先在每个字符开头说明 **该字符未来在二进制流中会使用多少位**，从而不会读错下一个字符。

**Unicode 表示一个字符可以使用 1 - 4 个字节。**UTF-8 是这样做的，第一个字节如果开头位是0，那么就说明该字符只占用一个字节，否则后面有几个 1，就说明该字符需要几个字节来表达。

具体如下：

| 1 字节 | 0xxxxxxx                            |
| ------ | ----------------------------------- |
| 2 字节 | 110xxxxx 10xxxxxx                   |
| 3 字节 | 1110xxxx 10xxxxxx 10xxxxxx          |
| 4 字节 | 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx |

解释：如果它表示一个字符只需要 1 个字节，那么表示的就是 ASCII 字符集，从0 -> 127。如果需要 2 个及以上字节表示，那么**第一个字节的前 n 位是 1 ，第 n+1 位是 0，后面每个字节的前两位均为 10（n 是所需字节数）。**

所以按照上述规则，“知”字的二进制为：

```
30693（十进制） -> U+77E5(十六进制) -> 0111 0111 1110 0101（二进制）
```

所以对应的 UTF-8 编码为：**1110**0111 **10**011111 **10**100101，你只需要从低位到高位依次按规则填充即可。

看到这里，我想有思考的读者应该有疑问，为什么原本只需要两字节就能表示的字经过 UTF-8 转换后需要三个字节了，这不是白白地增加内存消耗吗？你可以回忆一下哈夫曼编码的构建结果：将长短不同的**二进制位段**直接放在一起却不会读错，是因为他们没有共同前缀。这里的原理类似，要解决地问题是 **怎么确保长短不同的字符不会重合**。由于有的字符只需要一个字节，而有的需要两个，三个，n 个。当他们堆放在一起时，怎么保证不会出现读少，读多？

解释这个问题，我举个例子，“你”字**假设**表示的十六进制是 A，“我”是 B，“你我”是 AA，“好”是 AB，那我将“你好”放一起时表示就是 AAB，它为什么不是“你你我”，或者“你我我”？

我相信如果你看懂了这个例子，应该就能明白为什么 UTF-8 被称为变长编码了。

这段的标题是 UTF，上面只说了 UTF-8，其实常用的还有 UTF-16，UTF-8 是将一个字节作为一个单位，随着所需字节数量的不同给他们不同的前缀，当计算机读到第一个字节时，通过判断前面连续 1 的个数就能判断未来多少位属于这个字符的范围,，从而解决了不会读错的问题。而 UTF-16 是**将两个字节作为了一个单位**。原理类似，有兴趣的读者可以自己再去探索，我相信你会有更多的发现 :)

## 验证结果，梳理思路

我们可以写一个简单的 Go 语言程序来验证这个结果：

```go
package main

import "fmt"

func main() {
 str := "hello,狗狼"
 fmt.Println(len(str))
 fmt.Println(len([]rune(str)))
}
```

输出结果为：

```shell
12
8

Process finished with exit code 0
```

这里需要说明的是，str 字符串的底层实现就是一个字节数组，根据上面所说的汉字占用 3 个字节，总字节长度为 6+3+3=12，而转换为 rune 类型后，所有字符都占用一个 Unicode **Code Point**（码点），所以占用了共 8 个字符，共 8 个码点。

综上所述，ASCII 和 Unicode 都是一种字符集，代表了字符与数字间的一一对应关系。而 UTF 是一种变长的字符编码规范。而 rune 是 Go 语言中的一个变量类型，一个 rune 代表了一个 Unicode 码点单位。

因个人能力有限，有疏漏之处欢迎和我交流  :)
