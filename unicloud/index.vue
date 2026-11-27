<!--
  首页 · 树枝 / 春
  复制到 pages/index/index.vue 即可（整份替换原文件）。

  ★ 建议顺手改一处：pages.json 里本页的 style 加上 "navigationStyle": "custom"
    否则 H5 / App 顶部会多一条系统标题栏，压住画面最上面一行小字。
    不改也能正常显示，只是无法满屏。

  ★ 图片：/static/shuzhi.jpg（你项目里已经有这张，不用再放）
  ★ 一切动效都是纯 CSS，没有额外依赖、没有 WebGL，免费版扛得住
-->

<template>
	<view class="tree-stage">
		<!-- 背景：照片（cover 裁切，绝不拉伸）+ 蒙版 + 颗粒 + 细边框 -->
		<view class="tree-photo"></view>
		<view class="tree-veil"></view>
		<view class="tree-grain"></view>
		<view class="tree-frame"></view>

		<view class="tree-content">
			<!-- 顶部小标 -->
			<view class="tree-top tree-rv">
				<view class="tree-mark">
					<view class="tree-dot"></view>
					<text class="tree-wordmark">TWO</text>
				</view>
				<text class="tree-date">2026 · 春</text>
			</view>

			<!-- 正文：三组短句 -->
			<view class="tree-poem">
				<view class="tree-rule tree-rv"></view>

				<view class="tree-stanza tree-rv d1">
					<text class="tree-no">01</text>
					<view class="tree-lines">
						<text class="tree-line">笔直向上</text>
						<text class="tree-line">褪尽枯黄的碎叶</text>
					</view>
				</view>

				<view class="tree-stanza tree-rv d2">
					<text class="tree-no">02</text>
					<view class="tree-lines">
						<text class="tree-line">最高处的枝桠</text>
						<text class="tree-line">不留一丝多余的重量</text>
					</view>
				</view>

				<view class="tree-stanza tree-rv d3 is-last">
					<text class="tree-no">03</text>
					<view class="tree-lines">
						<text class="tree-line">干干净净，伸向天空</text>
						<text class="tree-line">白花细碎，蓝天透亮</text>
					</view>
				</view>
			</view>

			<!-- 页脚：署名 + 云函数入口 -->
			<view class="tree-foot tree-rv">
				<text class="tree-note">UNI-APP · ALIPAY CLOUD</text>
				<view class="tree-entry" hover-class="tree-entry-on" @click="callMyCloud">
					<text class="tree-entry-text">云函数 · 试一下</text>
					<text class="tree-arrow">↗</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
const callMyCloud = () => {
	// 调用你已经上传的云函数
	uniCloud.callFunction({
		name: 'getinfo', // 必须跟你建的云函数文件夹名字一模一样
		success: (res) => {
			console.log('前端拿到数据啦：', res.result);
			uni.showModal({
				title: '云端返回',
				content: res.result.msg,
				showCancel: false
			});
		},
		fail: (err) => {
			console.error('调用失败了：', err);
			uni.showModal({
				title: '错误',
				content: '调用失败，请检查底部控制台',
				showCancel: false
			});
		}
	});
};
</script>

<style>
/* 只作用于 .tree-stage 内部，不会污染其他页面 */
.tree-stage {
	position: fixed;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
	overflow: hidden;
	color: #ffffff;
	background: #06121c;
	font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", "SimSun", serif;
	-webkit-font-smoothing: antialiased;
	text-rendering: optimizeLegibility;
	--px: clamp(22px, 6.2vw, 100px);
	--py: clamp(30px, 4.6vh, 54px);
	--mono: ui-monospace, "SF Mono", Menlo, Consolas, "Courier New", monospace;
}
.tree-stage,
.tree-stage * {
	box-sizing: border-box;
}

/* ---------- 背景照片：cover 只裁不压 + 极慢推移 ----------
   用 CSS 背景做裁切，任何窗口比例都不会把树枝压扁。
   background-position 的第二个值越小越靠上：0% 留住全部枝尖，8% 微裁，30% 更靠枝干中部。
   （微信小程序不支持本地路径背景图；以后若要发小程序，改回 <image mode="aspectFill" />） */
.tree-photo {
	position: absolute;
	left: -2%;
	top: -2%;
	width: 104%;
	height: 104%;
	background-image: url("/static/shuzhi.jpg");
	background-size: cover;
	background-position: 50% 8%;
	background-repeat: no-repeat;
	filter: saturate(1.04) contrast(1.02) brightness(1.06);
	animation: tree-photo-in 2.4s cubic-bezier(.2, .65, .2, 1) both,
		tree-photo-drift 64s ease-in-out 2.4s infinite alternate;
}
@keyframes tree-photo-in {
	from { opacity: 0; }
	to { opacity: 1; }
}
@keyframes tree-photo-drift {
	from { transform: scale(1); }
	to { transform: scale(1.045); }
}

/* ---------- 蒙版：左侧压暗承字，上下轻压做层次 ---------- */
.tree-veil {
	position: absolute;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
	pointer-events: none;
	background:
		linear-gradient(94deg, rgba(5, 14, 23, .72) 0%, rgba(5, 14, 23, .40) 24%, rgba(5, 14, 23, .08) 50%, rgba(5, 14, 23, 0) 66%),
		linear-gradient(0deg, rgba(5, 14, 23, .66) 0%, rgba(5, 14, 23, .10) 20%, rgba(5, 14, 23, 0) 42%),
		linear-gradient(180deg, rgba(5, 14, 23, .44) 0%, rgba(5, 14, 23, .04) 22%, rgba(5, 14, 23, 0) 36%);
}
.tree-grain {
	position: absolute;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
	pointer-events: none;
	opacity: .07;
	mix-blend-mode: soft-light;
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E");
}
.tree-frame {
	position: absolute;
	left: clamp(10px, 1.4vw, 18px);
	top: clamp(10px, 1.4vw, 18px);
	right: clamp(10px, 1.4vw, 18px);
	bottom: clamp(10px, 1.4vw, 18px);
	border: 1px solid rgba(255, 255, 255, .15);
	pointer-events: none;
}

/* ---------- 版心 ---------- */
.tree-content {
	position: absolute;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
	display: flex;
	flex-direction: column;
	padding: calc(var(--py) + env(safe-area-inset-top)) var(--px) calc(var(--py) + env(safe-area-inset-bottom));
}

.tree-top {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
}
.tree-mark {
	display: flex;
	align-items: center;
}
.tree-dot {
	width: 5px;
	height: 5px;
	background: rgba(255, 255, 255, .9);
	margin-right: .85em;
}
.tree-wordmark {
	font-family: var(--mono);
	font-size: clamp(10px, .7vw, 12px);
	letter-spacing: .36em;
	opacity: .86;
}
.tree-date {
	font-family: var(--mono);
	font-size: clamp(9.5px, .64vw, 11px);
	letter-spacing: .26em;
	opacity: .62;
	padding-top: 1px;
}

/* ---------- 诗句 ---------- */
.tree-poem {
	margin-top: auto;
	margin-bottom: auto;
	max-width: min(64vw, 660px);
	padding-top: 3vh;
}
.tree-rule {
	width: clamp(26px, 2.4vw, 38px);
	height: 1px;
	background: rgba(255, 255, 255, .5);
	margin-bottom: clamp(20px, 3.2vh, 34px);
}
.tree-stanza {
	display: flex;
	margin-bottom: clamp(18px, 3vh, 32px);
}
.tree-stanza.is-last {
	margin-bottom: 0;
}
.tree-no {
	font-family: var(--mono);
	font-size: 11px;
	letter-spacing: .1em;
	opacity: .38;
	padding-top: 1.2em;
	margin-right: clamp(12px, 1.2vw, 20px);
	flex: 0 0 auto;
}
.tree-lines {
	display: block;
}
.tree-line {
	display: block;
	font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", "SimSun", serif;
	font-weight: 400;
	font-size: clamp(26px, 2.5vw, 44px);
	line-height: 1.66;
	letter-spacing: .1em;
	color: rgba(255, 255, 255, .94);
	text-shadow: 0 1px 26px rgba(3, 10, 18, .3);
}
.tree-line + .tree-line {
	margin-top: .04em;
}
.tree-stanza.is-last .tree-line {
	color: #ffffff;
}

/* ---------- 页脚 ---------- */
.tree-foot {
	display: flex;
	justify-content: space-between;
	align-items: flex-end;
}
.tree-note {
	font-family: var(--mono);
	font-size: clamp(9.5px, .64vw, 11px);
	letter-spacing: .22em;
	opacity: .5;
	line-height: 1.9;
}
.tree-entry {
	display: flex;
	align-items: center;
	padding-bottom: 6px;
	border-bottom: 1px solid rgba(255, 255, 255, .3);
	transition: border-color .35s;
}
.tree-entry-on {
	border-color: rgba(255, 255, 255, .75);
}
.tree-entry-text {
	font-family: var(--mono);
	font-size: clamp(10px, .68vw, 12px);
	letter-spacing: .18em;
	color: rgba(255, 255, 255, .8);
}
.tree-arrow {
	font-family: var(--mono);
	font-size: clamp(10px, .68vw, 12px);
	color: rgba(255, 255, 255, .8);
	margin-left: .6em;
}

/* ---------- 入场：逐级升起 ---------- */
.tree-rv {
	opacity: 0;
	animation: tree-rise .95s cubic-bezier(.2, .7, .2, 1) forwards;
}
@keyframes tree-rise {
	from { opacity: 0; transform: translateY(16px); }
	to { opacity: 1; transform: none; }
}
.tree-top.tree-rv { animation-delay: .15s; }
.tree-rule.tree-rv { animation-delay: .42s; }
.tree-rv.d1 { animation-delay: .58s; }
.tree-rv.d2 { animation-delay: .78s; }
.tree-rv.d3 { animation-delay: .98s; }
.tree-foot.tree-rv { animation-delay: 1.28s; }

/* ---------- 手机：改成下压式蒙版 ---------- */
@media (max-width: 820px) {
	.tree-stage {
		--px: clamp(20px, 6vw, 32px);
	}
	.tree-veil {
		background:
			linear-gradient(180deg, rgba(5, 14, 23, .64) 0%, rgba(5, 14, 23, .10) 16%, rgba(5, 14, 23, 0) 32%),
			linear-gradient(0deg, rgba(4, 11, 18, .97) 0%, rgba(4, 11, 18, .94) 34%, rgba(4, 11, 18, .86) 55%, rgba(4, 11, 18, .55) 70%, rgba(4, 11, 18, .12) 82%, rgba(4, 11, 18, 0) 90%);
	}
	.tree-frame {
		left: 10px;
		top: 10px;
		right: 10px;
		bottom: 10px;
	}
	.tree-poem {
		max-width: none;
		margin-top: auto;
		margin-bottom: 0;
		padding: 0 0 clamp(24px, 4.4vh, 40px);
	}
	.tree-line {
		font-size: clamp(24px, 5.4vw, 36px);
		line-height: 1.7;
		letter-spacing: .055em;
		text-shadow: 0 1px 2px rgba(3, 10, 18, .4), 0 0 34px rgba(3, 10, 18, .6);
	}
	.tree-stanza {
		margin-bottom: clamp(16px, 2.6vh, 26px);
	}
	.tree-no {
		font-size: 10px;
		opacity: .5;
		padding-top: 1.3em;
		margin-right: 12px;
	}
	.tree-note {
		max-width: 58%;
		line-height: 1.8;
		letter-spacing: .16em;
	}
}

/* ---------- 横屏手机 / 矮窗口：把左侧压得更实，字才不被枝条吃掉 ---------- */
@media (max-height: 560px) {
	.tree-photo {
		filter: saturate(.96) contrast(1.04) brightness(.86);
	}
	.tree-veil {
		background:
			linear-gradient(94deg, rgba(5, 14, 23, .9) 0%, rgba(5, 14, 23, .76) 30%, rgba(5, 14, 23, .44) 56%, rgba(5, 14, 23, .06) 76%, rgba(5, 14, 23, 0) 86%),
			linear-gradient(0deg, rgba(5, 14, 23, .7) 0%, rgba(5, 14, 23, 0) 40%),
			linear-gradient(180deg, rgba(5, 14, 23, .5) 0%, rgba(5, 14, 23, 0) 30%);
	}
	.tree-line {
		font-size: clamp(18px, 3.4vh, 26px);
		line-height: 1.6;
	}
	.tree-stanza {
		margin-bottom: 14px;
	}
	.tree-poem {
		padding-top: 0;
	}
}

/* ---------- 尊重系统「减少动态效果」 ---------- */
@media (prefers-reduced-motion: reduce) {
	.tree-photo,
	.tree-rv {
		animation: none !important;
		opacity: 1 !important;
		transform: none !important;
	}
}

/*
  说明：这页靠 position:fixed 满屏，不受页面滚动影响。
  如果 pages.json 里没有给本页加 "navigationStyle": "custom"，
  H5 顶部会留一条 44px 的系统标题栏；这时把下面这行取消注释，
  让内容整体下移即可（加了 custom 就不要开，会多出空白）：

  .tree-stage { padding-top: 44px; }
*/
</style>