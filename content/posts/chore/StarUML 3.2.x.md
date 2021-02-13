---
title: "StarUML3.x 版本解包分析"
date: 2020-05-20 22:11:13
tags:
  - UML
  - 工具
---

由于软件工程基础课需要，搜索发现这个工具还算毕竟好用的，下载了这个工具发现需要注册码，遂进行一番查找，最后确定如下方法。之所以写博客记录下来是因为**有两个坑点**。

> OS：Windows 10 专业版。 
>
> 更新时间：2020/5/17
>
> StarUML版本：3.2.2

## 破解思路

该工具是用 Electron 框架所写，代码是通过 asar 工具打包而成，我们只需要利用该工具反编译出源代码，修改相关判断逻辑即可。

## 具体做法

### 下载安装 node

如果不会，自（bie）行（lai）解（zhao）决（wo）。

### 使用 cnpm 包管理工具下载 asar

由于众所周知的原因，用 cnpm 下载，先安装 cnpm并使用淘宝镜像源：

```shell
npm install -g cnpm --registry=https://registry.npm.taobao.org	// 下载 asar

cnpm install -g asar // 安装 asar
```

### 解压 asar 文件，修改源代码

找到 StarUML 安装目录里 resource 文件夹下的 app.asar 文件，执行解压：

```
asar extract app.asar app
```

#### 坑点一、解压盘符问题

由于 StarUML 默认安装位置是 C 盘，直接在 StarUML 的安装目录下执行会有权限问题，会报类似这种错误：

 ```
$ asar extract app.asar app
 internal/fs/utils.js:230
  throw err;
  ^
    
    Error: EPERM: operation not permitted, open 'app\package.json'
  at Object.openSync (fs.js:458:3)
  at Object.writeFileSync (fs.js:1279:35)
     at Object.module.exports.extractAll (C:\Users\shiluo\AppData\Roaming\npm\node_modules\asar\lib\asar.js:201:10)
     at Command.<anonymous> (C:\Users\shiluo\AppData\Roaming\npm\node_modules\asar\bin\asar.js:72:10)
     at Command.listener [as _actionHandler] (C:\Users\shiluo\AppData\Roaming\npm\node_modules\asar\node_modules\_commander@5.1.0@commander\index.js:413:31)
     at Command._parseCommand (C:\Users\shiluo\AppData\Roaming\npm\node_modules\asar\node_modules\_commander@5.1.0@commander\index.js:914:14)
     at Command._dispatchSubcommand (C:\Users\shiluo\AppData\Roaming\npm\node_modules\asar\node_modules\_commander@5.1.0@commander\index.js:865:18)
     at Command._parseCommand (C:\Users\shiluo\AppData\Roaming\npm\node_modules\asar\node_modules\_commander@5.1.0@commander\index.js:882:12)
     at Command.parse (C:\Users\shiluo\AppData\Roaming\npm\node_modules\asar\node_modules\_commander@5.1.0@commander\index.js:717:10)
     at Object.<anonymous> (C:\Users\shiluo\AppData\Roaming\npm\node_modules\asar\bin\asar.js:80:9) {
    errno: -4048,
    syscall: 'open',
   code: 'EPERM',
   path: 'app\\package.json'
   }
 ```

 解决方法：只需要把 app.asar 单独拿出来放其他盘比如你放 D 盘（不要在根目录，下面有解释），然后再次执行上面这个命令即可。

然后找到解压出来的源代码的 app/src/engine/license-manager.js 文件，大概在 120 行：

```javascript
checkLicenseValidity() {
  this.validate().then(() => {
    setStatus(this, true)
  }, () => {
    // setStatus(this, false)
    // UnregisteredDialog.showDialog()
    setStatus(this, true)
  })
}
```

可以很明显看到是一个 Promise ，成功了将注册状态设置为 true，否则设置为 false，并且弹窗提示。所以嘛。。就在这里下手，把逻辑改掉，如上图所示。

### 重新打包运行

```shell
asar pack app app.asar
```

#### 坑点二、打包路径问题

上面说到不要把解压得到的 app 目录放在根目录下，否则执行打包命令后会报这个错误，这里我拿 D 盘举个栗子：

```shell
$ asar pack app app.asar
(node:9504) UnhandledPromiseRejectionWarning: Error: EPERM: operation not permitted, mkdir 'D:\'
(node:9504) UnhandledPromiseRejectionWarning: Unhandled promise rejection. This error originated either by throwing inside of an async function without a catch block, or by rejecting a promise which was not handled with .catch(). To terminate the node process on unhandled promise rejection, use the CLI flag `--unhandled-rejections=strict` (see https://nodejs.org/api/cli.html#cli_unhandled_rejections_mode). (rejection id: 1)
(node:9504) [DEP0018] DeprecationWarning: Unhandled promise rejections are deprecated. In the future, promise rejections that are not handled will terminate the Node.js process with a non-zero exit code.
```

执行完后会得到一个 80 MB 左右的 asar 文件，拿它覆盖原安装包内的 asar 文件，运行 StarUML。

搞定。