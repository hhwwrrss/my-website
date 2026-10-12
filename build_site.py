#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Static gallery generator for 蓝猫果果.
Run this script after adding new photos; it regenerates thumbs/ + medium/ + index.html/style.css/script.js.
Deploy: push everything to GitHub, Cloudflare Pages auto-publishes.

布局说明：
  原图  -> originals/（仅本地存档，不进 git、不部署）
  缩略图 -> thumbs/   （相册网格，~600px，部署）
  灯箱图 -> medium/   （放大查看，~1600px，部署）
"""

import json
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("缺少 Pillow。请运行: pip install Pillow") from exc

ROOT = Path(__file__).resolve().parent
ORIGINALS_DIR = ROOT / "originals"
OUTPUT_DIR = ROOT / "public"
THUMB_DIR = OUTPUT_DIR / "thumbs"
THUMB_W = 600
THUMB_QUALITY = 82
MEDIUM_DIR = OUTPUT_DIR / "medium"
MEDIUM_W = 1600
MEDIUM_QUALITY = 80
AVATAR_SRC = ROOT / "images" / "avatar.png"
AVATAR_DST = OUTPUT_DIR / "images" / "avatar.png"

IMG_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

HTML_PATH = OUTPUT_DIR / "index.html"
CSS_PATH = OUTPUT_DIR / "style.css"
JS_PATH = OUTPUT_DIR / "script.js"


def collect_images():
    """Find all original photos inside originals/."""
    if not ORIGINALS_DIR.exists():
        return []
    imgs = []
    for p in sorted(ORIGINALS_DIR.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in IMG_SUFFIXES:
            continue
        imgs.append(p)
    return imgs


def ensure_output_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    MEDIUM_DIR.mkdir(parents=True, exist_ok=True)
    AVATAR_DST.parent.mkdir(parents=True, exist_ok=True)
    # Remove stale thumbs/mediums whose originals no longer exist.
    current = {p.name for p in collect_images()}
    for d in (THUMB_DIR, MEDIUM_DIR):
        for t in d.iterdir():
            if t.is_file() and t.name not in current:
                t.unlink()


def make_thumbnail(src: Path) -> Path:
    dst = THUMB_DIR / (src.stem + ".jpg")
    try:
        with Image.open(src) as im:
            # Handle transparent PNGs by compositing on white.
            if im.mode in ("RGBA", "P"):
                bg = Image.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P":
                    im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[3])
                im = bg
            else:
                im = im.convert("RGB")

            if im.width > THUMB_W:
                ratio = THUMB_W / im.width
                new_h = max(1, int(im.height * ratio))
                try:
                    resample = Image.Resampling.LANCZOS
                except AttributeError:
                    resample = Image.LANCZOS
                im = im.resize((THUMB_W, new_h), resample)

            im.save(dst, "JPEG", quality=THUMB_QUALITY, optimize=True)
    except Exception as exc:
        print(f"生成缩略图失败 {src.name}: {exc}")
        # Fallback: copy original as-is.
        shutil.copy2(src, dst)
    return dst


def make_medium(src: Path) -> Path:
    dst = MEDIUM_DIR / (src.stem + ".jpg")
    try:
        with Image.open(src) as im:
            if im.mode in ("RGBA", "P"):
                bg = Image.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P":
                    im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[3])
                im = bg
            else:
                im = im.convert("RGB")

            if im.width > MEDIUM_W:
                ratio = MEDIUM_W / im.width
                new_h = max(1, int(im.height * ratio))
                try:
                    resample = Image.Resampling.LANCZOS
                except AttributeError:
                    resample = Image.LANCZOS
                im = im.resize((MEDIUM_W, new_h), resample)

            im.save(dst, "JPEG", quality=MEDIUM_QUALITY, optimize=True)
    except Exception as exc:
        print(f"生成中等图失败 {src.name}: {exc}")
        shutil.copy2(src, dst)
    return dst


def build_gallery_data(images):
    data = []
    for img in images:
        thumb = make_thumbnail(img)
        medium = make_medium(img)
        with Image.open(img) as im:
            w, h = im.size
        data.append(
            {
                "full": f"medium/{medium.name}".replace("\\", "/"),
                "thumb": f"thumbs/{thumb.name}".replace("\\", "/"),
                "w": w,
                "h": h,
            }
        )
    return data


CSS = r""":root {
  --bg: #eef3fb;
  --bg-2: #e3ecf7;
  --card: rgba(255, 255, 255, 0.78);
  --text: #2c3e50;
  --muted: #5f738e;
  --primary: #5b8db8;
  --accent: #f4a261;
  --shadow: 0 8px 32px rgba(43, 59, 80, 0.12);
  --radius: 18px;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: linear-gradient(135deg, var(--bg) 0%, var(--bg-2) 100%);
  color: var(--text);
  line-height: 1.65;
  min-height: 100vh;
}

a {
  color: inherit;
  text-decoration: none;
}

/* Hero */
.hero {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 40px 24px;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 30%, rgba(91, 141, 184, 0.18) 0%, transparent 60%);
  pointer-events: none;
}

.hero-avatar {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: var(--shadow), 0 0 0 6px rgba(255, 255, 255, 0.6);
  animation: float 4s ease-in-out infinite;
  position: relative;
  z-index: 1;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.hero h1 {
  font-size: clamp(2.6rem, 8vw, 4.5rem);
  margin: 24px 0 12px;
  background: linear-gradient(90deg, #4a7ba5, #6fa8d8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  position: relative;
  z-index: 1;
  letter-spacing: -0.02em;
}

.hero .subtitle {
  font-size: clamp(1.1rem, 3vw, 1.45rem);
  color: var(--muted);
  max-width: 580px;
  margin: 0 auto 32px;
  position: relative;
  z-index: 1;
  line-height: 1.7;
}

.scroll-hint {
  position: absolute;
  bottom: 32px;
  color: var(--muted);
  font-size: 0.9rem;
  animation: bounce 2s infinite;
  z-index: 1;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); opacity: 0.6; }
  50% { transform: translateY(8px); opacity: 1; }
}

/* Sections */
section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 80px 24px;
}

.section-title {
  font-size: 2rem;
  text-align: center;
  margin-bottom: 44px;
  color: var(--text);
}

/* Stats */
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  max-width: 860px;
  margin: 0 auto;
}

.stat-card {
  background: var(--card);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: var(--radius);
  padding: 28px 18px;
  text-align: center;
  box-shadow: var(--shadow);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 14px 36px rgba(43, 59, 80, 0.16);
}

.stat-number {
  font-size: 2.3rem;
  font-weight: 700;
  color: var(--primary);
  line-height: 1.2;
}

.stat-label {
  color: var(--muted);
  margin-top: 6px;
  font-size: 0.95rem;
}

/* About */
.about-card {
  background: var(--card);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: var(--radius);
  padding: 36px;
  box-shadow: var(--shadow);
  max-width: 760px;
  margin: 0 auto;
  text-align: center;
  font-size: 1.08rem;
}

.about-card p {
  margin: 0 0 14px;
}

.about-card p:last-child {
  margin-bottom: 0;
}

/* Gallery */
.gallery {
  column-count: 3;
  column-gap: 18px;
}

.gallery-item {
  break-inside: avoid;
  margin-bottom: 18px;
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 4px 18px rgba(43, 59, 80, 0.1);
  cursor: zoom-in;
  transform: translateY(0);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  position: relative;
}

.gallery-item:focus-visible {
  outline: 3px solid var(--primary);
  outline-offset: 2px;
}

.gallery-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 14px 34px rgba(43, 59, 80, 0.18);
}

.gallery-item img {
  width: 100%;
  height: auto;
  display: block;
  transition: transform 0.5s ease;
}

.gallery-item:hover img {
  transform: scale(1.04);
}

.gallery-item::after {
  content: "\2764";
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  color: rgba(255, 255, 255, 0.92);
  background: rgba(91, 141, 184, 0.25);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.gallery-item:hover::after {
  opacity: 1;
}

/* Reveal animations — 加载时即显示，不依赖滚动触发（避免内容隐形） */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(28px); }
  to   { opacity: 1; transform: translateY(0); }
}

.reveal {
  animation: fadeUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
}

/* Lightbox */
.lightbox {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(18, 24, 32, 0.96);
  z-index: 100;
  padding: 20px;
}

.lightbox.active {
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox img {
  max-width: 92vw;
  max-height: 86vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
}

.lightbox .btn {
  position: absolute;
  background: rgba(255, 255, 255, 0.12);
  border: none;
  color: #fff;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  font-size: 1.6rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease, transform 0.2s ease;
  user-select: none;
}

.lightbox .btn:hover {
  background: rgba(255, 255, 255, 0.28);
  transform: scale(1.08);
}

.lightbox .close {
  top: 20px;
  right: 20px;
  font-size: 1.4rem;
}

.lightbox .arrow {
  top: 50%;
  transform: translateY(-50%);
}

.lightbox .arrow:hover {
  transform: translateY(-50%) scale(1.08);
}

.lightbox .prev {
  left: 16px;
}

.lightbox .next {
  right: 16px;
}

.lightbox .counter {
  position: absolute;
  bottom: 22px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.95rem;
  letter-spacing: 0.04em;
}

/* Footer */
footer {
  text-align: center;
  padding: 70px 24px 50px;
  color: var(--muted);
  font-size: 0.95rem;
}

footer p {
  margin: 6px 0;
}

/* Responsive */
@media (max-width: 900px) {
  .gallery { column-count: 2; }
  .stats { grid-template-columns: 1fr; max-width: 420px; }
}

@media (max-width: 560px) {
  .gallery { column-count: 1; }
  .hero-avatar { width: 130px; height: 130px; }
  .about-card { padding: 26px 22px; }
  .lightbox .arrow {
    top: auto;
    bottom: 70px;
    transform: none;
  }
  .lightbox .arrow:hover { transform: scale(1.08); }
  .lightbox .prev { left: 20px; }
  .lightbox .next { right: 20px; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  html { scroll-behavior: auto; }
}
"""


JS_TEMPLATE = r"""const GALLERY = __GALLERY_DATA__;

let currentIdx = 0;
const grid = document.getElementById("galleryGrid");
const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightboxImg");
const counter = document.getElementById("counter");

function renderGallery() {
  if (!GALLERY.length) {
    grid.innerHTML = "<p style='text-align:center;color:var(--muted)'>还没有照片哦。</p>";
    return;
  }

  grid.innerHTML = GALLERY.map((item, i) => {
    const ratio = item.w && item.h ? `${item.w}/${item.h}` : "auto";
    return `
      <div class="gallery-item" data-index="${i}" tabindex="0" role="button" aria-label="\u67e5\u770b\u7b2c ${i + 1} \u5f20">
        <img src="${item.thumb}" alt="\u679c\u679c\u7684\u7167\u7247" loading="lazy" decoding="async"
             width="${item.w || ""}" height="${item.h || ""}" style="aspect-ratio:${ratio}">
      </div>
    `;
  }).join("");

  grid.querySelectorAll(".gallery-item").forEach((el) => {
    el.addEventListener("click", () => openLightbox(parseInt(el.dataset.index, 10)));
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter") openLightbox(parseInt(el.dataset.index, 10));
    });
  });
}

function openLightbox(i) {
  currentIdx = i;
  updateLightbox();
  lightbox.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeLightbox() {
  lightbox.classList.remove("active");
  document.body.style.overflow = "";
}

function updateLightbox() {
  const item = GALLERY[currentIdx];
  lightboxImg.src = item.full;
  counter.textContent = `${currentIdx + 1} / ${GALLERY.length}`;
}

function next(e) {
  e.stopPropagation();
  currentIdx = (currentIdx + 1) % GALLERY.length;
  updateLightbox();
}

function prev(e) {
  e.stopPropagation();
  currentIdx = (currentIdx - 1 + GALLERY.length) % GALLERY.length;
  updateLightbox();
}

document.getElementById("closeBtn").addEventListener("click", closeLightbox);
document.getElementById("nextBtn").addEventListener("click", next);
document.getElementById("prevBtn").addEventListener("click", prev);

lightbox.addEventListener("click", (e) => {
  if (e.target === lightbox) closeLightbox();
});

document.addEventListener("keydown", (e) => {
  if (!lightbox.classList.contains("active")) return;
  if (e.key === "Escape") closeLightbox();
  if (e.key === "ArrowRight") next(e);
  if (e.key === "ArrowLeft") prev(e);
});

// Scroll reveal
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) entry.target.classList.add("active");
  });
}, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });

document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

renderGallery();
"""


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>蓝猫果果 · 纪念我的小蓝猫</title>
  <meta name="description" content="纪念我家蓝猫果果的个人网站，收藏我们一起度过的温暖时光。">
  <link rel="stylesheet" href="./style.css?v=20261012">
</head>
<body>
  <header class="hero">
    <img src="./images/avatar.png" alt="蓝猫果果" class="hero-avatar">
    <h1>蓝猫果果</h1>
    <p class="subtitle">每一张照片，都是一段温暖的回忆。<br>谢谢你曾来到我的世界。</p>
    <span class="scroll-hint">向下滚动 ↓</span>
  </header>

  <section id="about" class="reveal">
    <h2 class="section-title">关于果果</h2>
    <div class="about-card">
      <p>你是一只灰蓝色的小英国短毛猫，毛茸茸、软绵绵，总爱挑家里最舒服的地方蜷成一团。</p>
      <p>虽然你已经去了喵星，但手机里的每一张照片，都让我想起你打呼噜、伸懒腰、歪着头看我的样子。</p>
      <p>这个小网站，是我留给你的小小纪念。</p>
    </div>
  </section>

  <section id="stats" class="reveal">
    <div class="stats">
      <div class="stat-card"><div class="stat-number">__PHOTO_COUNT__</div><div class="stat-label">张照片</div></div>
      <div class="stat-card"><div class="stat-number">∞</div><div class="stat-label">无尽的想念</div></div>
      <div class="stat-card"><div class="stat-number">永远</div><div class="stat-label">活在我心里</div></div>
    </div>
  </section>

  <section id="gallery" class="reveal">
    <h2 class="section-title">果果的相册</h2>
    <div class="gallery" id="galleryGrid"></div>
  </section>

  <footer>
    <p>永远爱你，果果。</p>
    <p>Made with ❤️ by R一一</p>
  </footer>

  <div class="lightbox" id="lightbox">
    <button class="btn close" id="closeBtn" aria-label="关闭">✕</button>
    <button class="btn arrow prev" id="prevBtn" aria-label="上一张">‹</button>
    <img src="" alt="果果" id="lightboxImg">
    <button class="btn arrow next" id="nextBtn" aria-label="下一张">›</button>
    <div class="counter" id="counter">1 / __PHOTO_COUNT__</div>
  </div>

  <script src="./script.js?v=20261012"></script>
</body>
</html>
"""


def main():
    ensure_output_dirs()
    images = collect_images()
    if not images:
        print("未找到照片。请把照片放在本脚本同级目录下。")
        return

    print(f"发现 {len(images)} 张照片，开始生成...")
    data = build_gallery_data(images)

    # Write CSS
    CSS_PATH.write_text(CSS, encoding="utf-8")

    # Write JS
    js = JS_TEMPLATE.replace("__GALLERY_DATA__", json.dumps(data, ensure_ascii=False, indent=2))
    JS_PATH.write_text(js, encoding="utf-8")

    # Write HTML
    html = HTML_TEMPLATE.replace("__PHOTO_COUNT__", str(len(images)))
    HTML_PATH.write_text(html, encoding="utf-8")

    # Copy avatar into output dir
    if AVATAR_SRC.exists():
        shutil.copy2(AVATAR_SRC, AVATAR_DST)
    else:
        print(f"警告：未找到头像 {AVATAR_SRC}")

    print(f"完成。gallery 共 {len(data)} 张照片。")
    print(f"生成文件：{HTML_PATH.name}, {CSS_PATH.name}, {JS_PATH.name}")
    print(f"输出目录：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
