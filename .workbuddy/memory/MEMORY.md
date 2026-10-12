# 蓝猫果果网站项目笔记

## 部署流程
- 本地文件 → GitHub Desktop 推送到 GitHub → Cloudflare Pages 自动部署。
- 纯静态站点，无构建步骤。Cloudflare Pages 选择"No framework"，构建命令留空，输出目录用根目录 `/`。

## 站点结构
- `index.html` + `style.css` + `script.js`：页面主体。
- `images/avatar.png`：Hero 区头像。
- `thumbs/`：相册网格使用的 600px 缩略图。
- 根目录下的原图：灯箱点击后显示的大图。
- `build_site.py`：扫描根目录照片 → 生成缩略图 → 重新生成 HTML/CSS/JS。新增照片后运行一次即可。
