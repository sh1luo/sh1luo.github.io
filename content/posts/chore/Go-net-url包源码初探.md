---
title: "Go语言net/url包源码初探"
date: 2020-03-11 22:49:51
tags:
  - Go
  - 源码
  - 官方库
---

## 问题起因

问题的起因是最近需要写一个小工具，期间因为需要自己在服务器上搭建了一个 Web 服务来提供 RESTful API 接口，在请求接口的时候需要拼接 url，没有考虑到部分字符的编码问题，导致 [400 Bad Request](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/400) 错误。原来使用的是这样：

```go
// url := fmt.Sprintf("%ssearch?keywords=%s %s&limit=1", Mp3Server, name, singer)
// resp,err := http.Get(url)
// ...
```

这个 name 和 singer 都有可能是中文，直接请求服务器无法识别，所以导致 400 无效请求的错误。后来改成这样，就成功了：

```go
q := url.Values{}
q.Set("keywords", name+" "+singer)
q.Set("limit", "1")
u := url.URL{
	Scheme:   "http",
	Host:     "shiluo.design:3000",
	Path:     "search",
	RawQuery: q.Encode(), 				// 关键在这
}

resp, err := http.Get(u.String())
```

问题解决的关键就是在 `RawQuery: q.Encode()` 。由于我一直有看源码的习惯，我就 ctrl+左键跟进去把处理逻辑看了几遍，收获不小，特别记录下来。

## 整体处理逻辑

整个方法的主逻辑过程：

```go
// Encode encodes the values into ``URL encoded'' form
// ("bar=baz&foo=quux") sorted by key.
func (v Values) Encode() string {
	if v == nil {
		return ""
	}
	var buf strings.Builder
	keys := make([]string, 0, len(v))
	for k := range v {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		vs := v[k]
		keyEscaped := QueryEscape(k)
		for _, v := range vs {
			if buf.Len() > 0 {
				buf.WriteByte('&')
			}
			buf.WriteString(keyEscaped)
			buf.WriteByte('=')
			buf.WriteString(QueryEscape(v))
		}
	}
	return buf.String()
}
```

其最终目的是把类似 `http://shiluo.design:3000/search?keywords=海阔天空 beyond&limit=1` 这种的 URL 编码为服务器可识别的 `http://shiluo.design:3000/search?keywords=%E6%AD%8C%E6%9B%B2+%E6%AD%8C%E6%89%8B&limit=1` 这种格式的 URL。

遍历的 vs 就是某个 key 对应的所有 value 值，`buf.WriteByte('&')` 是在任何一次写入后追加 & 连接查询字符串。我们重点关注最后一行代码 `buf.WriteString(QueryEscape(v))` 。

## 深入剖析

> Values 是自定义的 type Values map\[string][]string 

处理过程是：判断 Values 是否为空，如果是返回空字符串。设置一个 Builder 用来构建未来需要返回的字符串。由于 url 的 query string 查询时一个 key 允许有多个 value，所以遍历每个 key 的所有value值，判定 key 值中是否有需要转义的字符，拿到转义处理后的字符串，然后通过 `buf.WriteString(keyEscaped)` 和 `buf.WriteByte('=')` 写入**一对 key-value 键值对** 。也就是说 key 判断转义了一次，它下面的 n 个 value 都判断转义了一次，最终**处理完一个 key 时，写入了 n 对键值对** 。其实最核心的逻辑在 `QueryEscape()` 这个函数。

```go
// QueryEscape escapes the string so it can be safely placed
// inside a URL query.
func QueryEscape(s string) string {
	return escape(s, encodeQueryComponent)
}

func escape(s string, mode encoding) string {
	spaceCount, hexCount := 0, 0
	for i := 0; i < len(s); i++ {
		c := s[i]
		if shouldEscape(c, mode) {
			if c == ' ' && mode == encodeQueryComponent {
				spaceCount++
			} else {
				hexCount++
			}
		}
	}

	if spaceCount == 0 && hexCount == 0 {
		return s
	}

	var buf [64]byte
	var t []byte

	required := len(s) + 2*hexCount
	if required <= len(buf) {
		t = buf[:required]
	} else {
		t = make([]byte, required)
	}

	if hexCount == 0 {
		copy(t, s)
		for i := 0; i < len(s); i++ {
			if s[i] == ' ' {
				t[i] = '+'
			}
		}
		return string(t)
	}

	j := 0
	for i := 0; i < len(s); i++ {
		switch c := s[i]; {
		case c == ' ' && mode == encodeQueryComponent:
			t[j] = '+'
			j++
		case shouldEscape(c, mode):
			t[j] = '%'
			t[j+1] = upperhex[c>>4]
			t[j+2] = upperhex[c&15]
			j += 3
		default:
			t[j] = s[i]
			j++
		}
	}
	return string(t)
}

// Return true if the specified character should be escaped when
// appearing in a URL string, according to RFC 3986.
//
// Please be informed that for now shouldEscape does not check all
// reserved characters correctly. See golang.org/issue/5684.
func shouldEscape(c byte, mode encoding) bool {
	// §2.3 Unreserved characters (alphanum)
	if 'a' <= c && c <= 'z' || 'A' <= c && c <= 'Z' || '0' <= c && c <= '9' {
		return false
	}

	if mode == encodeHost || mode == encodeZone {
		// mode 不符合，与这段代码无关....
	}

	switch c {
	case '-', '_', '.', '~': // §2.3 Unreserved characters (mark)
		return false

	case '$', '&', '+', ',', '/', ':', ';', '=', '?', '@': // §2.2 Reserved characters (reserved)
		// Different sections of the URL allow a few of
		// the reserved characters to appear unescaped.
		switch mode {
		case encodePath: // §3.3
			// The RFC allows : @ & = + $ but saves / ; , for assigning
			// meaning to individual path segments. This package
			// only manipulates the path as a whole, so we allow those
			// last three as well. That leaves only ? to escape.
			return c == '?'

		case encodePathSegment: // §3.3
			// The RFC allows : @ & = + $ but saves / ; , for assigning
			// meaning to individual path segments.
			return c == '/' || c == ';' || c == ',' || c == '?'

		case encodeUserPassword: // §3.2.1
			// The RFC allows ';', ':', '&', '=', '+', '$', and ',' in
			// userinfo, so we must escape only '@', '/', and '?'.
			// The parsing of userinfo treats ':' as special so we must escape
			// that too.
			return c == '@' || c == '/' || c == '?' || c == ':'

		case encodeQueryComponent: // §3.4
			// The RFC reserves (so we must escape) everything.
			return true

		case encodeFragment: // §4.1
			// The RFC text is silent but the grammar allows
			// everything, so escape nothing.
			return false
		}
	}

	if mode == encodeFragment {
		// mode 不符合，与这段代码无关....
	}

	// Everything else must be escaped.
	return true
}
```

这个函数判断了**哪些字符需要转义，并对这些字符进行处理**。这里就举例说明一下 `http://shiluo.design:3000/search?keywords=海阔天空 beyond&limit=1` 这个 keywords 参数的转换过程，因为其包含了中文字符和空格。

首先通过包裹了 `escape` 通过参数 mode 将过滤类型设置为 **URL 编码类型** 。`shouldEscape(c,mode)` 判定哪些字符需要转义，里面根据 RFC 规范进行了各种判断就是为了找出必须要转义的字符。

首先是大小写字母和一些规范内的正常字符是不需要转义的，其余的比如我们参数中的中文和空格都不在这些字符内，所以最终不满足任何一种条件，返回 true，也就是需要转义。所以遍历过“海阔天空 beyond”这个 value 后，统计出来的 hex 值是 4,space 值是 1。

因为一个汉字例如“海”转义后是“%E6”，由原来的一个字节变为了三个字节，所以要根据上面统计出来的 hex 值扩大容量。如果 buf 能够容纳就直接获取，否则使用 make 重新分配内存。最终遍历“海阔天空 beyond”这个字符串，`j` 是用来移动数组下标的。

> ```go
> const upperhex = "0123456789ABCDEF"
> ```

**过程如下**：“海”是需要转义的，所以将第一个字符设置为 %，紧接着取“海”这个字占用的字节数组 [230 181 183] 的第一位s[0] 230 右移4位是 14 对应是 ‘E’。第二位是和 15 按位与，结果是6，然后将下标指针向后移动三位，指向下一个存储位置。处理这个过程直到遇到空格，然后将空格替换为'+'，后面的英文正常不变，处理完成。

**最终我们可以看出，所谓转义就是取这个字符字节数组的第一位，按照一定规则将这个字符转换为十六进制的过程。所以到这里也很容易理解为什么我之前这样拼接 URL 会导致错误，之前一直没发现问题也可能是因为拼接的都是英文字符。** 

最后，每次看完官方的某些代码还是不得不感叹处理逻辑的紧密，考虑之周到。还是要多多看别人源码，不断学习。