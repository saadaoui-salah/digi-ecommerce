import io

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from apps.catalog.models import Category, Product

PALETTES = [
    ((14, 165, 233), (15, 23, 42)),
    ((6, 182, 212), (8, 47, 73)),
    ((2, 132, 199), (30, 41, 59)),
    ((13, 148, 136), (15, 42, 57)),
    ((59, 130, 246), (23, 37, 84)),
    ((56, 189, 248), (12, 32, 66)),
    ((45, 212, 191), (19, 55, 66)),
    ((99, 102, 241), (23, 37, 84)),
    ((34, 211, 238), (10, 36, 51)),
    ((96, 165, 250), (17, 34, 64)),
    ((20, 184, 166), (20, 30, 48)),
]


class Command(BaseCommand):
    help = "Generate placeholder images for categories/products and a short video demo."

    @staticmethod
    def _initials(name):
        words = [word for word in name.split() if word]
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        return (words[0][:2].upper() if words else "DG")

    def _image(self, name, index):
        top, bottom = PALETTES[index % len(PALETTES)]
        width, height = 960, 620
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        for y in range(height):
            blend = y / height
            color = tuple(
                int(top[i] + (bottom[i] - top[i]) * blend) for i in range(3)
            )
            draw.line([(0, y), (width, y)], fill=color)

        glow = Image.new("L", (width, height), 0)
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse(
            (width * 0.55, -80, width * 1.15, height * 0.6), fill=90
        )
        glow = glow.filter(ImageFilter.GaussianBlur(60))
        highlight = Image.new("RGB", (width, height), (255, 255, 255))
        image = Image.composite(highlight, image, glow.point(lambda v: v // 3))
        image = image.convert("RGB")

        draw = ImageDraw.Draw(image)
        initials = self._initials(name)
        font = ImageFont.load_default(size=120)
        box = draw.textbbox((0, 0), initials, font=font)
        text_w = box[2] - box[0]
        text_h = box[3] - box[1]
        draw.text(
            ((width - text_w) / 2 - box[0], (height - text_h) / 2 - box[1]),
            initials,
            font=font,
            fill=(255, 255, 255),
        )

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def _video(self):
        import shutil
        import subprocess
        import tempfile
        from pathlib import Path

        if not shutil.which("ffmpeg"):
            self.stdout.write("ffmpeg not found; skipping demo video.")
            return None
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as handle:
            output = Path(handle.name)
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi",
                    "-i", "gradients=s=640x360:d=4:speed=0.08:c0=#0EA5E9:c1=#0F172A",
                    "-frames:v", "120", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(output),
                ],
                check=True,
            )
            return output.read_bytes()
        finally:
            output.unlink(missing_ok=True)

    def handle(self, *args, **options):
        for index, category in enumerate(Category.objects.all()):
            if category.image:
                continue
            category.image.save(
                f"{category.slug}.png",
                ContentFile(self._image(category.name, index + 1)),
                save=True,
            )
            self.stdout.write(f"image: category {category.slug}")

        for index, product in enumerate(Product.objects.all()):
            if not product.image:
                product.image.save(
                    f"{product.slug}.png",
                    ContentFile(self._image(product.name, index)),
                    save=True,
                )
                self.stdout.write(f"image: product {product.slug}")

            gallery_count = product.gallery_images.count()
            for variant in range(gallery_count, 2):
                data = self._image(product.name, index + variant + 1)
                product.gallery_images.create(
                    sort_order=variant,
                    image=ContentFile(data, f"{product.slug}-{variant + 1}.png"),
                )
                self.stdout.write(f"gallery: product {product.slug} #{variant + 1}")

            if not product.video:
                data = self._video()
                if data:
                    product.video.save(
                        f"{product.slug}.mp4", ContentFile(data), save=True
                    )
                    self.stdout.write(f"video: product {product.slug}")
