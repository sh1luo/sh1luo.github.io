---
title: "https为什么安全，绝对安全吗"
date: 2021-01-27 15:57:50
tags:
  - HTTPS
  - 安全
---

> 截图均使用了 [Wireshark](https://www.wireshark.org/) 工具进行抓包分析。

## 简介

HTTP 是无状态协议，这一特性极大地增强了 HTTP 协议的灵活性，设计的高度自由随着发展也带来了各种问题。比如明文传输且无法验证通信方身份，不适合在安全场景下使用等等。

所以提出了 HTTPS 的概念。HTTPS  并不是新的协议，而是 `HTTP over SSL/TLS`，也就是使用了 SSL/TLS 加密的 HTTP，解决了 HTTP 不安全的问题。SSL（Secure Sockets Layer） 是 TLS（Transport Layer Security） 的前身，SSL 经历了三个版本的变迁，后来升级为了 TLS，TLS 主要有 1.0、1.1、1.2 和 1.3，版本越高兼容性越不好，现在大部分正在从 1.1 到 1.2 的迁移，部分使用 1.3，我们可以使用 Wireshark 过滤一下进行简单查看。

![Wireshark截图](https://gitee.com/sh1luo/imgs/raw/master/imgs/640.png)

需要注意的是，应用了 HTTPS 后通信效率会变低，毕竟需要进行额外的握手，加解密步骤。 

## 证书

不管什么版本的 SSL/TLS，只使用对称加密和非对称加密也是不够的，因为无法解决中间人攻击，都需要配合证书来完成整个验证过程。所以在说明 TLS/1.2 与 TLS/1.3 之前有必要介绍一下证书的几个概念。

证书的作用有两个：

- 确保通信目标的身份。
- 确认你的身份。

其实就是确认通信双方的身份，而不是中间某个第三者。再结合非对称加密与对称加密，就可以解决 HTTP 的三大问题，明文传输，消息篡改，窃听。证书的整个流程如下图：

![ca](https://gitee.com/sh1luo/imgs/raw/master/imgs/ca.png)

### 加密与签名

这里有一点需要注意，非对称加密中的公私钥有两种用法，被称为 **加密** 和 **签名** ，很多人容易搞混。不过需要记住不变的是 **私钥永远需要保密**，不能公布。

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

到现在，我们已经利用证书机制确保了通信双方的身份，解决了不安全的问题之一。

## TLS1.2

RSA 是一种非对称加密算法，也是可以用来加密和签名的算法之一。先来看一下 TLS1.2 版本握手步骤：

![tls-hs-ecdhe](https://gitee.com/sh1luo/imgs/raw/master/imgs/tls-hs-ecdhe.png)

TLS/1.2 的共需要 4 次握手，花费两个 RTT（Round-Trip Time，RTT），加上 TCP 握手就是一共 7 次握手，再加上 HTTP 的一次报文交换，一共需要 4.5 个 RTT。

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

   3. 向客户端发送 Server Key Exchange 消息，传递 ECDHE 算法的参数，也被称为 server_params，还有签名等信息。这个过程还会被签名，即签名这个摘要值：

      ```
      SHA256(client_random + server_random + server_params)
      ```

      ![dhe-params](https://gitee.com/sh1luo/imgs/raw/master/imgs/dhe-params.png)

   4. 向客户端发送可选的消息 CertificateRequest，验证客户端的证书。因为 TLS 握手是一个双向认证的过程，所以服务端可以向客户端发送请求来验证客户端身份。这个验证的回复再第三次握手阶段发出。

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

你可能会问，为什么 非对称加密这么强什么都能干为啥还要再使用对称加密呢？

原因是**对称加密效率高**，大致是非对称加密的几十上百倍。

## TLS1.3

TLS/1.2 握手过程繁琐，验证复杂，所以花费时间也是非常长，TLS/1.3 版本就对此做出了优化。主要优化有两个方面。

### 安全

TLS/1.3 精简了加密套件， 

### 性能

## 总结