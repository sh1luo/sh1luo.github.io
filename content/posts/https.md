---
title: "https为什么安全"
date: 2021-01-27 15:57:50
tags:
  - HTTPS
  - 安全
---

> 截图均使用了 [Wireshark](https://www.wireshark.org/) 工具进行抓包分析。

HTTPS  并不是一种新的协议，而是 `HTTP over SSL/TLS`，也就是使用了 SSL/TLS 加密的 HTTP，解决了 HTTP 不安全的问题。SSL（Secure Sockets Layer） 是 TLS（Transport Layer Security） 的前身，它们都处在 OSI 七层模型中的会话层。SSL 经历了三个版本的变迁，后来升级为了 TLS，TLS 主要有 1.0、1.1、1.2 和 1.3，现在大部分正在从 1.1 到 1.2 的迁移，部分使用 1.3，我们可以使用 Wireshark 过滤一下进行简单查看。

![Wireshark截图](https://gitee.com/sh1luo/imgs/raw/master/imgs/640.png)

需要注意的是，应用了 HTTPS 后通信效率会变低，毕竟需要进行额外的握手，加解密步骤。 

SSL/TLS 加密手段本质就是进行若干次握手，协商出一个对称加密的密钥用于后续加密通信。主要可以分为两种方式，RSA 和 ECDH。RSA 方式也在 TLS/1.3 中正式被废除。下面我们分别来看。 

## 证书

不管什么版本的 SSL/TLS，只使用对称加密和非对称加密也是不够的，因为无法解决 **中间人攻击**，都需要配合证书来完成整个验证过程。所以在说明 TLS/1.2 与 TLS/1.3 之前有必要介绍一下证书的几个概念。

证书的作用有两个：

- 确保通信目标的身份。
- 确认你的身份。

其实就是确认通信双方的身份，而不是中间某个第三者。再结合非对称加密与对称加密，就可以解决 HTTP 的三大问题，明文传输，消息篡改，窃听。证书的整个流程如下图：

![ca](https://gitee.com/sh1luo/imgs/raw/master/imgs/ca.png)

### 加密与签名

这里有一点需要注意，非对称加密中 RSA 算法有一个非常好的特性，它的公私钥有两种用法，被称为 **加密** 和 **签名** ，很多人容易搞混。不过需要记住不变的是 **私钥永远需要保密**，不能公布。

- 前者是使用公钥加密，私钥解密。将公钥发布出去，只有自己才能获得加密信息，用于 **保护信息**。
- 后者是私钥加密，公钥解密。用于 **判断信息是否被篡改**。

加密很好理解，签名可以这样理解：私钥加密的签名其他人无法伪造（其他人没有私钥），而你将经过私钥加密的信息和未加密明文还有公钥一起交付，对方就可以用公钥去解密（公钥是公开的），然后比对，如果一致了就说明信息没有被篡改，否则已经被改过了，抛弃。

整个过程可以参考上图，证书的过程就是使用了加密和签名两种手段。

### 信任链

在你申请到 CA 的证书并部署，在客户端请求时返回后，客户端的验证过程是有信任链验证的。你可以随便打开一个部署了 HTTPS 的站点，点击锁图标查看证书路径。

![](https://gitee.com/sh1luo/imgs/raw/master/imgs/image-20210129114612091.png)

可以看到你的证书是处于最下级，也就是三级证书，这个证书是由上一级证书机构 Secure Site CA G2 签发的，由于它不是根证书，无法认为它可靠，所以要再向上级寻找直到根证书。然后使用根证书公钥验证二级证书，依次向下，直到目标服务器的证书。

为什么要这样一步一步验证好多次呢？

因为我们只相信根证书，而根证书是部署在操作系统上的，是被我们信任的。Windows 10 系统可以通过

````
控制面板 -> 搜索证书 -> 管理计算机证书 
````

方式之一来查看本地根证书。

![](https://gitee.com/sh1luo/imgs/raw/master/imgs/Snipaste_2021-01-28_21-32-27.png)

好了，你现在应该大致明白了证书的验证过程，再来一张图看总结一下。

![640 (1)](https://gitee.com/sh1luo/imgs/raw/master/imgs/640%20(1).png)

至此，我们已经利用证书机制确保了通信双方的身份，解决了不安全的问题之一。

## TLS1.2/ECDHE

先来看一下最常见的 ECDHE 方式握手步骤图：

![tls-hs-ecdhe](https://gitee.com/sh1luo/imgs/raw/master/imgs/tls-hs-ecdhe.png)

TLS/1.2 的共需要 4 次握手，花费两个 RTT（Round-Trip Time，RTT），如果加上 TCP 握手就是一共 7 次握手，再加上 HTTP 的一次报文交换，一共需要 4.5 个 RTT。

握手过程较为麻烦，大致过程如下：

1. 客户端向服务端发送 **Client Hello** 消息，其中携带客户端支持的**协议版本**，**加密套件**，压缩算法、**客户端生成的随机数** 以及扩展列表，不过安全的客户端一般不允许压缩，会传递一个 null 作为唯一的压缩算法，来避免 [CRIME attack](https://en.wikipedia.org/wiki/CRIME) 。

   ![client-hello](https://gitee.com/sh1luo/imgs/raw/master/imgs/client-hello.png)

2. 服务端收到客户端发来的协议版本、加密算法等信息后：
   1. 向客户端发送 **Server Hello** 消息，并选择其中一个协议版本、加密方法、会话 ID 以及 **服务端生成的随机数**；这里的加密方法格式非常规范：

      ```
      TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
      ```

      上面的加密套件的意思是：生成密钥所使用的算法为 ECDHE_RSA，后续通信使用的对称加密算法 128位的AES，分组模式是 GCM（对称加密的关键），哈希摘要算法 SHA256。

      ![server-hello](https://gitee.com/sh1luo/imgs/raw/master/imgs/server-hello.png)

   2. 向客户端发送 Certificate 消息，即服务端的证书链，其中包含证书支持的域名、发行方和有效期等信息；

      ![](https://gitee.com/sh1luo/imgs/raw/master/imgs/server-certificate.png)

   3. 向客户端发送 Server Key Exchange 消息，传递 ECDHE 算法的参数，也被称为 server_params，还有签名等信息。这个过程还会被签名：

      ```
      SHA256(client_random + server_random + server_params)
      ```

      ![dhe-params](https://gitee.com/sh1luo/imgs/raw/master/imgs/dhe-params.png)

   4. 向客户端发送可选的消息 CertificateRequest，验证客户端的证书。因为 TLS 握手是一个双向认证的过程，所以服务端可以向客户端发送请求来验证客户端身份。这个验证的回复在客户端第三次握手阶段发出。

   5. 向客户端发送 Server Hello Done 消息，通知服务端已经发送了全部的相关信息；

      ![server-hello-done](https://gitee.com/sh1luo/imgs/raw/master/imgs/server-hello-done.png)
3. 客户端收到服务端的协议版本、加密方法、会话 ID 以及证书等信息后，验证服务端的证书；
   1. 向服务端发送 Client Key Exchange 消息，包含客户端生成的公钥字符串，然后计算得到预主密钥（Pre Master Secret），再利用之前在客户端和服务端分别产生的两个随机数，还有伪随机数函数也就是 SHA256 哈希摘要函数，最终计算得到最终的主密钥（Master Key）；

      ```
      master_secret = PRF(pre_master_secret, "master secret", client_random + server_random)[0..47]
      ```

      ![client-dhe-key (1)](https://gitee.com/sh1luo/imgs/raw/master/imgs/client-dhe-key%20(1).png)

   2. 向服务端发送 Change Cipher Spec 消息，通知服务端后面的数据段会加密传输。

   3. 向服务端发送 Finished 消息，其中包含加密后的握手信息。这个消息包含之前通信的所有信息以及之前的两个随机字符串，求哈希值后再加密，确保服务端能正常解密并且确认无误，还能避免重放攻击。
4. 服务端收到 Change Cipher Spec 和 Finished 消息后计算得到预主密钥（Pre Master Secret），然后同样流程计算得到最终的主密钥；
   1. 向客户端发送 Change Cipher Spec 消息，通知客户端后面的数据段会加密传输；
   2. 向客户端发送 Finished 消息，验证客户端的 Finished 消息并完成 TLS 握手；

TLS 握手的关键在于利用通信双方生成的随机字符串和服务端的公钥生成一个双方经过协商后的密钥，通信的双方可以使用这个对称的密钥加密消息防止中间人的监听和攻击，保证通信的安全。

这么多繁琐的步骤就是为了验证两方身份的情况下协商出一个对称加密的密钥。

你可能会问：

- 非对称加密这么强什么都能干为啥还要再使用对称加密呢？
  - 原因是**对称加密效率高**，是非对称加密的上百倍。你可以使用 openssl 工具的 speed 子命令来查看不同加密算法的性能测试。
- HTTPS 通信是一个双向的过程，服务端怎么确认客户端身份呢？
  - 其实这是个可选项，比如网上银行这种场景，服务端会为客户端颁发证书，要求客户端在第三次握手时通过 `client certificate` 发送证书让服务端走一遍验证流程，确认客户端身份。

## 传统RSA

之所以说是传统 RSA，是因为使用了 RSA 公钥加密预主密钥（Pre-Master Key）。流程和 ECDH 的方式差不多，少了服务端的 **Server Key Exchange** 消息。这种方式的缺点是因为不具备 **前向保密性**，也就是说如果黑客一直收集你的加密信息，如果在未来某一个你的私钥泄露或者被计算出来了，你以前所有的加密信息都会被破解。

这也是为什么 ECDHE 算法最终在 TLS1.3 被保留，它在加密过程中使用临时产生的随机数作为椭圆曲线的参数来生成主密钥，这样就算私钥泄露，由于拿不到当时的随机密钥，也是没用的。主要流程如下：

![rsa](https://gitee.com/sh1luo/imgs/raw/master/imgs/rsa.png)

## TLS1.3

TLS1.3 为了解决向下兼容的问题，不能直接修改协议报文里的协议版本字段，这样会引起识别错误，导致 TLS 握手失败。所以就通过扩展字段来解决兼容问题：

```
Handshake Protocol: Client Hello
    Version: TLS 1.2 (0x0303)
    Extension: supported_versions (len=11)
        Supported Version: TLS 1.3 (0x0304)
        Supported Version: TLS 1.2 (0x0303)
```

主要优化有两个方面。

### 增强安全

TLS/1.3 精简了许多选项：

- 只保留 AES、ChaCha20 对称加密算法
- 分组模式只能用 GCM、CCM 和 Poly1305
- 消息摘要算法只能用 SHA256、SHA384
- 密钥交换算法只有 ECDHE 和 DHE
- 椭圆曲线也只剩下 P-256（也称为 secp256r1，openssl 里叫 prime256v1） 和 x25519（最安全最快速） 等5种。

> openssl 是知名的安全工具，几乎包含了所有公开的算法，你可以使用openssl speed命令来测试aes与rsa1024或rsa2048的速度，来直观的感受一下它们的速度差异。
>
> 我们平时在服务端需要生成一对公私要来交给 CA 或者其他用途的时候，一般也是使用 openssl 工具。

加密套件只剩下 5 种了，看看之前的十几个套件。。

![new_suit](https://gitee.com/sh1luo/imgs/raw/master/imgs/new_suit.jpg)

### 优化性能

客户端第一次握手：

```
Handshake Protocol: Client Hello
    Version: TLS 1.2 (0x0303)
    Random: cebeb6c05403654d66c2329…
    Cipher Suites (18 suites)
        Cipher Suite: TLS_AES_128_GCM_SHA256 (0x1301)
        Cipher Suite: TLS_CHACHA20_POLY1305_SHA256 (0x1303)
        Cipher Suite: TLS_AES_256_GCM_SHA384 (0x1302)
    Extension: supported_versions (len=9)
        Supported Version: TLS 1.3 (0x0304)
        Supported Version: TLS 1.2 (0x0303)
    Extension: supported_groups (len=14)
        Supported Groups (6 groups)
            Supported Group: x25519 (0x001d)
            Supported Group: secp256r1 (0x0017)
    Extension: key_share (len=107)
        Key Share extension
            Client Key Share Length: 105
            Key Share Entry: Group: x25519
            Key Share Entry: Group: secp256r1
```

服务端第二次握手：

```
Handshake Protocol: Server Hello
    Version: TLS 1.2 (0x0303)
    Random: 12d2bce6568b063d3dee2…
    Cipher Suite: TLS_AES_128_GCM_SHA256 (0x1301)
    Extension: supported_versions (len=2)
        Supported Version: TLS 1.3 (0x0304)
    Extension: key_share (len=36)
        Key Share extension
            Key Share Entry: Group: x25519, Key Exchange length: 32
```

TLS1.2 需要两个 RTT 完成握手，TLS1.3 优化为了一个 RTT。

具体的做法还是利用了扩展（因为要向下兼容，就像 HTTP 扩展可以无限增加首部字段一样）。

客户端第一次握手就发送自己这边的椭圆曲线参数，服务端也回复自己的参数。然后就可以生成主密钥了。

![tls13](https://gitee.com/sh1luo/imgs/raw/master/imgs/tls13.png)

TLS1.3 还多了一个 Vertificate Verify，也就是服务端用自己的私钥把以前的椭圆曲线参数等信息签名，确保消息没有被篡改。

## 总结

说了这么多，我们回到最初的问题，https 为什么安全，我想可以大致总结如下：

整体上通过引入第三方 CA 和证书机制验证双方身份，加密确保消息不会被窃听，签名确保消息不会被篡改解决了 HTTP 三大不安全问题。

如果你从 HTTP -> 传统RSA -> TLS1.2 -> TLS1.3 一路看过来就会发现，技术的变化也是需要时间的，有许多设计并不是一开始就完美无缺，**许多方案总是需要实践的检验才能被人们认可**。

