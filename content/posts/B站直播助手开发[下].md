---
title: Go+QML开发的跨平台桌面直播助手[下]
date: 2020-03-13 13:22:23
tags:
  - WebSocket
  - Go
---

# Go + QML

结合上节的分析，开发的思路的大致流程我画了个图，大概是这样：

![流程图](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/go_qml_flowchart.png)

> 因为是需要面向用户的，又考虑到 Go 语言的特殊性（可以直接调用 C/C++ 代码，GUI 官方不支持），最后决定使用 Qml 来呈现前端，与 Go 语言利用插槽和信号进行通信。

处理思路是创建一个协程池来处理不同类型的包数据。判断每个包内所有子包类型，将接收的未处理的字节数组直接送入对应协程池中的管道。因为代码也比较简单，就是简单的 WebSocket 通信。

```go
// 客户端实例
type Client struct {
	RoomID      uint32				// 房间 ID
	Online      uint32				// 用来判断人气是否变动
	Conn        *websocket.Conn		// 连接后的对象
	IsConnected bool
}
```

```go
// 使用了"github.com/gorilla/websocket"这个包，也可以自己升级 tcp 到 websocket
u := url.URL{Scheme: "wss", Host: DanMuServer, Path: "/sub",}
conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
if err != nil {
	return nil, err
}

// 发送包函数
func SendPackage(conn *websocket.Conn, packetlen uint32, magic uint16, ver uint16, typeID uint32, param uint32, data []byte) (err error) {
	packetHead := new(bytes.Buffer)

	if packetlen == 0 {
		packetlen = uint32(len(data) + 16)
	}
	var pdata = []interface{}{
		packetlen,
		magic,
		ver,
		typeID,
		param,
	}

	// 将包的头部信息以大端序，二进制形式写入字节数组
	for _, v := range pdata {
		if err = binary.Write(packetHead, binary.BigEndian, v); err != nil {
			return
		}
	}

	// 将包内数据部分追加到数据包内
	sendData := append(packetHead.Bytes(), data...)

	if err = conn.WriteMessage(websocket.BinaryMessage, sendData); err != nil {
		// fmt.Println("c.conn.Write err: ", err)
		return
	}

	return
}
```

拼接 URL 是使用的官方提供的 url 包，发送包数据要注意的是发送的是二进制数据流，所以要用 binary.Write 以二进制，且在网络上传输是大端序方式写入字节数组。

![心跳包上行](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/up.png)

心跳包上行是通过发送两个空的对象，所以我把这个固定的数直接粘贴下来转为字节数组后，创建一个 go 协程，按照每 30 秒一次的时间间隔发送就好。

```go
func (c *Client) HeartBeat() {
	for {
		if c.IsConnected {
			obj := []byte("5b6f626a656374204f626a6563745d")
			if err := util.SendPackage(c.Conn, 0, 16, 1, 2, 1, obj); err != nil {
				continue
			}
            // 每 30 秒发一次
			time.Sleep(30 * time.Second)
		}
	}
}
```

心跳包下行是还是一个固定的包首部，只携带了一个 4 字节大小的实体就是直播间人气值，所以我只需要每次和 c.Online 进行比较，及时修改人气数就可以了。

![心跳包下行](https://blogimagee.oss-cn-beijing.aliyuncs.com/images/down.png)

最后一个问题就是**对每个包的所有子包依次进行判断，防止信息量过大的时候有漏掉的情况**，思路是读取完第一个包后，根据第一个包的大小找到第二个包的偏移位置继续读取，直到达到末尾，里面的`ByteArrToDecimal`是自己写的一个将读取到的十进制字节数组转换为十进制表示数的方法函数，也附带在下方了，如果有更好的实现可以告诉我，我也是自己脑洞大开临时写的....有可能有更简单的实现。。。。

```go
for len(inflated) > 0 {
	l := util.ByteArrToDecimal(inflated[:4])
	c := json.Get(inflated[16:l], "cmd").ToString()
	switch c {
		case "DANMU_MSG":
			p.DanmuSrc <- string(inflated[16:l])
		case "SEND_GIFT":
			p.GiftSrc <- string(inflated[16:l])
		case "WELCOME", "WELCOME_GUARD":
			p.WelCome <- string(inflated[16:l])
	}
	inflated = inflated[l:]
}

// 返回十六进制字节数组表示数的十进制形式
func ByteArrToDecimal(src []byte) (sum int) {
	if src == nil {
		return 0
	}
    // 将读取的十进制字节数组数据编码为字符串，再转换为字节数组，方便后续进行逐字节处理
	b := []byte(hex.EncodeToString(src))
	l := len(b)
    // 从低位开始
	for i := l - 1; i >= 0; i-- {
		base := int(math.Pow(16, float64(l-i-1)))
		var mul int
		if int(b[i]) >= 97 {
			mul = int(b[i]) - 87
		} else {
			mul = int(b[i]) - 48
		}

		sum += base * mul
	}
	return
}
```

其余的与 Qml 进行通信的第三方包用的是 qamel，也可以使用比较广泛，功能大而全的 therecipe/qt ，是因为这个库比较小巧，安装使用简单，所以采用了这个。通信部分非常简单，就是使用了信号和插槽，整个程序包括了弹幕礼物进场点歌功能一共 500+ 行，有些代码略冗余，还需要凝练。如果大家有任何想法都可以跟我交流，不限于博客写法，代码规范，开发思路等等，欢迎！

## 总结

其实从有这个程序的想法到现在落地开发完成，也是走了不少的弯路的。一开始以为那些被压缩了的“乱码”是被加密的结果，自己又配置了 `sslkey.log`文件使用 Wireshark 解密，结果自然是白忙活一场。关键还是还是协议分析这块不够熟练，对网络理解不够。还有在连接弹幕服务器的时候尝试使用了 net 包下 net.Dial 进行通信，结果报错 `GetInfoW` 方法类找不到，当时只知道 ws 是基于 tcp，后来才知道单纯 tcp 根本无法与 ws 服务器连接，这一点说到底还是自己对连接过程理解不够。经过这个小项目，让自己对网络这一块的重要程度有了新的认识，决定要好好学习这些内容，还有 Go 语言的实操，协程池的使用，与 Qml 的通信。总体来说收获还是不小，以后还是要多上手练习。