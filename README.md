<h1>Count Anywhere</h1>

A tool for counting anything easily.

一个让计数更轻松的工具。

View documentation at [count-anywhere.readthedocs.io](https://count-anywhere.readthedocs.io/en/latest/).

# Quick Start 快速开始

## Start 启动
```shell
# Installation
python -m pip install count-anywhere
python -m count_anywhere

# Boot
count_anywhere
```

## 基础操作

程序启动后会挂在系统托盘里。
![Icon in system tray. 图标在系统托盘里。](./doc/img/icon_in_system_tray.jpg)



# Congiurations 配置

Configuration file is `config.yml`.

配置文件是 `config.yml`。

## Enable Debug Mode 启用调试模式

```yaml
debug: true
```

What will happen:
- After taking a screenshot, the marker editor will not stay on top.

会发生什么：
- 在截屏后，标记编辑器不会置顶。

# Feature 功能

- 手动放置、修改标记。
- 引入其他算法自动放置标记。
- 统计标记数量。
- 导出计数结果

# About 关于

## Why Count Anywhere is here? 为什么 Count Anywhere 出现在这？

市面上其实有很多有用的自动细胞计数工具，包括作为软件的 cellpose 和作为一体化硬件的某品牌细胞计数机。
不可否认，这些工具很好用，但是无论是哪一种方法都存在一些不足或者说是制约因素：

<table style="text-align: center;">
 <tr>
  <td>名称</td>
  <td>类别</td>
  <td>价格</td>
  <td>样本</td>
  <td>效率</td>
  <td>准确度</td>
 </tr>
 <tr>
  <td>流式细胞仪</td>
  <td>仪器</td>
  <td>昂贵</td>
  <td>细胞悬液</td>
  <td><i>较慢*</i></td>
  <td>近似</td>
 </tr>
 <tr>
  <td>细胞计数机</td>
  <td>软件（传统算法）</td>
  <td>一般</td>
  <td>显微图像/细胞玻片</td>
  <td>快速</td>
  <td>（传统算法可能无法应对复杂的情况）</td>
 </tr>
 <tr>
  <td>ImageJ 或 Fiji</td>
  <td>软件（传统算法）</td>
  <td>免费</td>
  <td>显微图像</td>
  <td><i>一般**</i></td>
  <td>（传统算法可能无法应对复杂的情况）</td>
 </tr>
 <tr>
  <td>神经网络模型（如 Cellpose/SAM）</td>
  <td>软件（神经网络）</td>
  <td>需要一定的算力资源；低计算资源可能也行，但需要较长的时间</td>
  <td>显微图像</td>
  <td>快速</td>
  <td>良好（小概率产生幻觉（错误））</td>
 </tr>
 <tr>
  <td>手动计数</td>
  <td>人工</td>
  <td>低廉/免费</td>
  <td>显微图像</td>
  <td>缓慢</td>
  <td>还行（易被干扰，但可以通过校验提高准确度）</td>
 </tr>
</table>

&#42; 毕竟流式细胞仪不是专门用来计数的，效率在这不适合比较。

&#42;&#42; 其实际效率取决于选取的插件与设计的处理流程。

因此，我认为需要一种结合了传统方法与现代工具的工作流以及一个配套软件——Cellpose：
1. （算力允许的情况下）（可选地）使用传统算法或神经网络模型来进行初步的自动标记。
2. 人工放置、修正、移除标记。
3. 导出统计数据。 

（不太会Java，所以不是很想写一个ImageJ插件。同时，我想随便整个玩具项目试试😋）
